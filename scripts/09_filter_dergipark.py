"""Filter the DergiPark JSONL harvest into a parquet ready for embedding.

Filters (mirroring scripts/02_filter_data.py for theses):
  1. language is Turkish (`tr`)
  2. abstract_tr non-empty
  3. abstract_tr >= 50 words
  4. title_tr non-empty
  5. deduplicate by article_id

Output schema is unified with the YÖK thesis schema so the same Chroma
indexing code can ingest both. Distinguishing field: `source_type`.

  thesis  metadata: tez_no = str(int)        e.g. "12345"
  article metadata: tez_no = "art-{article_id}"  e.g. "art-1704902"

Output:
  data/derived/dergipark_filtered.parquet
  data/derived/dergipark_filter_report.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
JSONL_PATH = ROOT / "data" / "raw" / "dergipark.jsonl"
DERIVED = ROOT / "data" / "derived" / "dergipark_filtered.parquet"
REPORT = ROOT / "data" / "derived" / "dergipark_filter_report.json"

MIN_WORDS = 50
WS_RE = re.compile(r"\s+")


def _wc(text: str) -> int:
    return 0 if not text else len(WS_RE.findall(text.strip())) + 1


def main() -> int:
    if not JSONL_PATH.exists():
        print(f"[!] Missing {JSONL_PATH}. Run scripts/05_harvest_dergipark.py first.", file=sys.stderr)
        return 1

    DERIVED.parent.mkdir(parents=True, exist_ok=True)

    print(f"[+] Reading {JSONL_PATH}")
    rows = []
    skipped = {"json_error": 0, "no_lang_tr": 0, "empty_abstract": 0,
               "short_abstract": 0, "empty_title": 0, "empty_id": 0}

    with JSONL_PATH.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped["json_error"] += 1
                continue

            # Filter 1: Turkish
            lang = (rec.get("language") or "").lower().strip()
            if not lang.startswith("tr"):
                skipped["no_lang_tr"] += 1
                continue

            abstract_tr = (rec.get("abstract_tr") or "").strip()
            if not abstract_tr:
                skipped["empty_abstract"] += 1
                continue

            if _wc(abstract_tr) < MIN_WORDS:
                skipped["short_abstract"] += 1
                continue

            title_tr = (rec.get("title_tr") or "").strip()
            if not title_tr:
                skipped["empty_title"] += 1
                continue

            article_id = (rec.get("article_id") or "").strip()
            if not article_id:
                skipped["empty_id"] += 1
                continue

            year_raw = rec.get("year") or 0
            try:
                year = int(year_raw) if year_raw else 0
            except (TypeError, ValueError):
                year = 0

            subjects = rec.get("subjects") or []
            subject_str = " ; ".join(s for s in subjects if s) if isinstance(subjects, list) else str(subjects or "")

            rows.append({
                "tez_no": f"art-{article_id}",
                "source_type": "article",
                "title_tr": title_tr,
                "title_en": (rec.get("title_en") or "").strip(),
                "author": (rec.get("authors") or "").strip(),
                "advisor": "",
                "location": (rec.get("publisher") or "").strip(),
                "subject": subject_str,
                "year": year,
                "pages": 0,
                "degree": "",
                "pdf_url": (rec.get("url") or "").strip(),
                "language": lang,
                "abstract_tr": abstract_tr,
                "abstract_en": (rec.get("abstract_en") or "").strip(),
                "journal": (rec.get("journal") or "").strip(),
            })

    initial = len(rows) + sum(skipped.values())
    print(f"[+] Read {initial:,} JSONL rows")
    for k, v in skipped.items():
        if v:
            print(f"    -{k:18s}: {v:,}")
    print(f"    after filters: {len(rows):,}")

    df = pd.DataFrame(rows)

    # Filter 5: dedupe
    before = len(df)
    df = df.drop_duplicates(subset=["tez_no"], keep="first").reset_index(drop=True)
    skipped["duplicate_id"] = before - len(df)
    if skipped["duplicate_id"]:
        print(f"    -duplicate_id      : {skipped['duplicate_id']:,}")
    print(f"    final              : {len(df):,}")

    df.to_parquet(DERIVED, index=False)
    print(f"[+] Wrote {DERIVED}  ({DERIVED.stat().st_size/1024/1024:.1f} MB)")

    # Year + journal stats
    year_dist = df["year"].value_counts().sort_index().to_dict()
    journals = df["journal"].value_counts().head(15).to_dict()

    REPORT.write_text(json.dumps({
        "raw_path": str(JSONL_PATH),
        "derived_path": str(DERIVED),
        "initial_rows": initial,
        "final_rows": len(df),
        "skipped": skipped,
        "min_words": MIN_WORDS,
        "year_min": int(min(year_dist) if year_dist else 0),
        "year_max": int(max(year_dist) if year_dist else 0),
        "year_distribution": {str(k): int(v) for k, v in year_dist.items()},
        "top_15_journals": journals,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
