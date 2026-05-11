"""Sample N random DergiPark articles, download PDFs, parse, report yield.

Output:
  data/audit/dergipark_pdf_samples/<article_id>.pdf  (raw PDF)
  data/audit/dergipark_pdf_samples/<article_id>.txt  (extracted text)
  data/audit/dergipark_pdf_audit.json                 (summary metrics)
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
PARQUET = ROOT / "data" / "derived" / "dergipark_filtered.parquet"
OUT_DIR = ROOT / "data" / "audit" / "dergipark_pdf_samples"
AUDIT_JSON = ROOT / "data" / "audit" / "dergipark_pdf_audit.json"

HEADERS = {"User-Agent": "tr-academic-audit/0.1 (research project)"}
PDF_LINK_RE = re.compile(r'href="(/[a-z]{2}/download/article-file/\d+)"')

N_SAMPLE = 100
SEED = 42
TIMEOUT = 30
POLITE_DELAY = 0.5


def find_pdf_url(landing_html: str) -> str | None:
    m = PDF_LINK_RE.search(landing_html)
    if m:
        path = m.group(1)
        return f"https://dergipark.org.tr{path}"
    return None


def extract_text(pdf_bytes: bytes) -> tuple[str, int, dict]:
    """Returns (text, page_count, info_dict). Raises on parse failure."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page in doc:
        pages.append(page.get_text())
    text = "\n".join(pages)
    info = {
        "page_count": doc.page_count,
        "is_encrypted": doc.is_encrypted,
        "metadata": dict(doc.metadata) if doc.metadata else {},
    }
    doc.close()
    return text, info["page_count"], info


def main():
    if not PARQUET.exists():
        print(f"[!] {PARQUET} not found", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(PARQUET, columns=["tez_no", "pdf_url", "subject", "year"])
    print(f"[+] Loaded {len(df):,} records")

    # Filter to valid years (drop year=7969 etc.)
    df = df[(df["year"] >= 1995) & (df["year"] <= 2026)].reset_index(drop=True)
    print(f"    {len(df):,} after year filter")

    rng = random.Random(SEED)
    indices = rng.sample(range(len(df)), N_SAMPLE)

    results = []
    total_text_chars = 0
    success_landing = 0
    success_pdf_link = 0
    success_download = 0
    success_parse = 0

    t0 = time.time()
    for i, idx in enumerate(indices, 1):
        row = df.iloc[idx]
        aid = str(row["tez_no"])
        landing = row["pdf_url"]
        subject = (row.get("subject") or "")[:50]

        entry = {
            "i": i,
            "article_id": aid,
            "landing_url": landing,
            "subject": subject,
            "year": int(row["year"]),
            "pdf_url": None,
            "pdf_bytes": 0,
            "text_chars": 0,
            "page_count": 0,
            "error": None,
        }

        try:
            r = requests.get(landing, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code != 200:
                entry["error"] = f"landing http {r.status_code}"
                results.append(entry); print(f"  [{i:>3}/{N_SAMPLE}] {aid} FAIL landing {r.status_code}")
                time.sleep(POLITE_DELAY); continue
            success_landing += 1

            pdf_url = find_pdf_url(r.text)
            if not pdf_url:
                entry["error"] = "no pdf link in landing"
                results.append(entry); print(f"  [{i:>3}/{N_SAMPLE}] {aid} FAIL no-pdf-link")
                time.sleep(POLITE_DELAY); continue
            success_pdf_link += 1
            entry["pdf_url"] = pdf_url

            r2 = requests.get(pdf_url, headers=HEADERS, timeout=TIMEOUT)
            if r2.status_code != 200 or len(r2.content) < 1024:
                entry["error"] = f"pdf http {r2.status_code} size={len(r2.content)}"
                results.append(entry); print(f"  [{i:>3}/{N_SAMPLE}] {aid} FAIL pdf-dl {r2.status_code}")
                time.sleep(POLITE_DELAY); continue
            success_download += 1
            entry["pdf_bytes"] = len(r2.content)

            # Save PDF
            (OUT_DIR / f"{aid}.pdf").write_bytes(r2.content)

            try:
                text, pages, _ = extract_text(r2.content)
                entry["text_chars"] = len(text)
                entry["page_count"] = pages
                # Save text
                (OUT_DIR / f"{aid}.txt").write_text(text, encoding="utf-8")
                success_parse += 1
                total_text_chars += len(text)
                print(f"  [{i:>3}/{N_SAMPLE}] {aid} OK {pages}p {len(text):,} chars")
            except Exception as e:
                entry["error"] = f"parse: {e}"
                print(f"  [{i:>3}/{N_SAMPLE}] {aid} FAIL parse: {e}")

        except Exception as e:
            entry["error"] = f"network: {e}"
            print(f"  [{i:>3}/{N_SAMPLE}] {aid} FAIL net: {e}")

        results.append(entry)
        time.sleep(POLITE_DELAY)

    elapsed = time.time() - t0
    summary = {
        "n_sample": N_SAMPLE,
        "elapsed_sec": round(elapsed, 1),
        "success": {
            "landing_page_200": success_landing,
            "pdf_link_found": success_pdf_link,
            "pdf_downloaded": success_download,
            "pdf_parsed": success_parse,
        },
        "yield": {
            "total_text_chars": total_text_chars,
            "avg_chars_per_article": round(total_text_chars / max(success_parse, 1)),
            "est_tokens_per_article": round(total_text_chars / max(success_parse, 1) / 4),
            "rate_articles_per_min": round(success_parse / (elapsed / 60), 1),
        },
        "per_record": results,
    }
    AUDIT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print(f"[+] Done in {elapsed/60:.1f} min")
    print(f"    landing OK: {success_landing}/{N_SAMPLE}")
    print(f"    pdf link found: {success_pdf_link}/{N_SAMPLE}")
    print(f"    pdf downloaded: {success_download}/{N_SAMPLE}")
    print(f"    pdf parsed: {success_parse}/{N_SAMPLE}")
    print(f"    avg chars/article: {summary['yield']['avg_chars_per_article']:,}")
    print(f"    avg tokens/article: ~{summary['yield']['est_tokens_per_article']:,}")
    print(f"    Audit summary: {AUDIT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
