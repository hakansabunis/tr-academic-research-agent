"""Parallel resumable DergiPark full-text PDF harvester for a filtered subset.

Usage:
    python data/audit/_harvest_dergipark_pdfs.py \
        --candidates data/audit/dergipark_stem_candidates.parquet \
        --limit 5000 \
        --workers 4 \
        --out-dir data/audit/dergipark_full_text \
        --year-min 2018

Outputs:
    <out-dir>/                    one .txt per article, named <tez_no>.txt
    <out-dir>/_state.json         tracks completed/failed for resume
    <out-dir>/_yield_report.json  final yield + size summary
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
import pymupdf

HEADERS = {"User-Agent": "tr-academic-audit/0.1 (research project)"}
TIMEOUT = 30
PDF_LINK_RE = re.compile(r'href="(/[a-z]{2}/download/article-file/\d+)"')


def find_pdf_url(landing_html: str) -> str | None:
    m = PDF_LINK_RE.search(landing_html)
    if m:
        return f"https://dergipark.org.tr{m.group(1)}"
    return None


def process_one(aid: str, landing: str, out_dir: Path, polite_delay: float) -> dict:
    """Download + parse one article. Returns result dict, never raises."""
    out_txt = out_dir / f"{aid}.txt"
    if out_txt.exists():
        chars = out_txt.stat().st_size
        return {"aid": aid, "status": "cached", "text_chars": chars}

    result = {"aid": aid, "status": "fail", "text_chars": 0, "error": None}
    try:
        r = requests.get(landing, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            result["error"] = f"landing_http_{r.status_code}"
            return result
        pdf_url = find_pdf_url(r.text)
        if not pdf_url:
            result["error"] = "no_pdf_link"
            return result
        time.sleep(polite_delay)
        r2 = requests.get(pdf_url, headers=HEADERS, timeout=TIMEOUT)
        if r2.status_code != 200 or len(r2.content) < 1024:
            result["error"] = f"pdf_http_{r2.status_code}_size_{len(r2.content)}"
            return result

        doc = pymupdf.open(stream=r2.content, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        page_count = doc.page_count
        doc.close()

        out_txt.write_text(text, encoding="utf-8")
        result["status"] = "ok"
        result["text_chars"] = len(text)
        result["pages"] = page_count
    except requests.RequestException as e:
        result["error"] = f"network: {type(e).__name__}"
    except Exception as e:
        result["error"] = f"parse: {type(e).__name__}: {str(e)[:80]}"

    return result


class StateTracker:
    def __init__(self, state_path: Path):
        self.path = state_path
        self.lock = threading.Lock()
        if state_path.exists():
            self.state = json.loads(state_path.read_text(encoding="utf-8"))
        else:
            self.state = {"completed": {}, "started_at": time.time()}

    def is_done(self, aid: str) -> bool:
        return aid in self.state["completed"]

    def mark(self, aid: str, result: dict):
        with self.lock:
            self.state["completed"][aid] = {
                "status": result["status"],
                "chars": result["text_chars"],
                "error": result.get("error"),
            }
            # Persist every 50 records
            if len(self.state["completed"]) % 50 == 0:
                self._save()

    def _save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def save_final(self):
        with self.lock:
            self.state["completed_at"] = time.time()
            self._save()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True,
                        help="Parquet with tez_no, pdf_url, subject, year columns")
    parser.add_argument("--out-dir", type=Path, default=Path("data/audit/dergipark_full_text"))
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--year-min", type=int, default=2018)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--polite-delay", type=float, default=0.5,
                        help="Per-worker delay between requests")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_parquet(args.candidates)
    df = df[df["year"] >= args.year_min].reset_index(drop=True)
    print(f"[+] Loaded {len(df):,} candidates (year>={args.year_min})")

    if "pdf_url" not in df.columns:
        # Join with the original filtered parquet to get landing URL
        orig = pd.read_parquet(
            Path("data/derived/dergipark_filtered.parquet"),
            columns=["tez_no", "pdf_url"],
        )
        before = len(df)
        df = df.merge(orig, on="tez_no", how="left")
        df = df[df["pdf_url"].notna()].reset_index(drop=True)
        print(f"[+] Joined pdf_url: {before:,} -> {len(df):,} after non-null filter")

    # Random sample
    rng = random.Random(args.seed)
    n = min(args.limit, len(df))
    indices = rng.sample(range(len(df)), n)
    targets = df.iloc[indices][["tez_no", "pdf_url", "subject", "year"]].to_dict("records")
    print(f"[+] Targets: {len(targets):,} articles ({args.workers} workers, {args.polite_delay}s/worker delay)")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    state_path = args.out_dir / "_state.json"
    tracker = StateTracker(state_path)
    print(f"[+] Resume: {len(tracker.state['completed']):,} already done")

    # Filter out already-done
    pending = [t for t in targets if not tracker.is_done(t["tez_no"])]
    print(f"[+] Pending: {len(pending):,}")

    if not pending:
        print("[=] Nothing to do.")
        return 0

    t0 = time.time()
    ok = fail = cached = 0
    total_chars = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(process_one, t["tez_no"], t["pdf_url"], args.out_dir, args.polite_delay): t
            for t in pending
        }
        for i, fut in enumerate(as_completed(futures), 1):
            t = futures[fut]
            res = fut.result()
            tracker.mark(t["tez_no"], res)
            if res["status"] == "ok":
                ok += 1
                total_chars += res["text_chars"]
            elif res["status"] == "cached":
                cached += 1
                total_chars += res["text_chars"]
            else:
                fail += 1
            if i % 50 == 0 or i == len(futures):
                elapsed = time.time() - t0
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(futures) - i) / rate if rate > 0 else 0
                print(
                    f"  [{i:>5}/{len(futures)}] ok={ok} cached={cached} fail={fail} "
                    f"{total_chars/1024/1024:.1f}MB | {rate:.1f}/s | ETA {eta/60:.0f}m",
                    flush=True,
                )

    tracker.save_final()

    # Yield report
    elapsed = time.time() - t0
    yield_path = args.out_dir / "_yield_report.json"
    yield_path.write_text(json.dumps({
        "limit": args.limit,
        "year_min": args.year_min,
        "workers": args.workers,
        "polite_delay": args.polite_delay,
        "n_pending": len(pending),
        "ok": ok,
        "cached": cached,
        "fail": fail,
        "total_chars": total_chars,
        "est_tokens": total_chars // 4,
        "elapsed_sec": round(elapsed, 1),
        "rate_per_sec": round(ok / elapsed, 2) if elapsed > 0 else 0,
    }, indent=2), encoding="utf-8")

    print()
    print(f"[+] Done in {elapsed/60:.1f} min")
    print(f"    ok={ok}  cached={cached}  fail={fail}")
    print(f"    total chars: {total_chars:,}  (~{total_chars//4:,} tokens)")
    print(f"    yield report: {yield_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
