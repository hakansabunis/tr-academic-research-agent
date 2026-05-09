"""Quality-filter the raw 650K thesis dataset down to a clean derived parquet.

Filters (applied in order, each row counted):
  1. abstract_tr non-empty
  2. abstract_tr >= 50 words
  3. title_tr non-empty
  4. tez_no unique (deduplicate keeping first)

Also does light cleanup:
  - Strip surrounding whitespace on string columns
  - Coerce year to int (NaN -> 0)
  - Normalize line endings in abstracts

Output: data/derived/abstracts_filtered.parquet + filter_report.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "abstracts_raw.parquet"
DERIVED = ROOT / "data" / "derived" / "abstracts_filtered.parquet"
REPORT = ROOT / "data" / "derived" / "filter_report.json"

MIN_WORDS = 50
WS_RE = re.compile(r"\s+")


def _wc(text: str) -> int:
    return 0 if not text else len(WS_RE.findall(text.strip())) + 1


def _norm_str(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def main() -> int:
    if not RAW.exists():
        print(f"[!] Run scripts/01_fetch_data.py first — missing {RAW}", file=sys.stderr)
        return 1

    DERIVED.parent.mkdir(parents=True, exist_ok=True)

    print(f"[+] Loading {RAW}")
    df = pd.read_parquet(RAW)
    initial = len(df)
    print(f"[+] {initial:,} rows loaded")

    # Normalize string columns
    str_cols = [
        "title_tr", "title_en", "author", "advisor", "location",
        "subject", "index", "status", "degree", "language",
        "pdf_url", "abstract_tr", "abstract_en",
    ]
    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].apply(_norm_str)

    # Coerce year
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)

    drops = {}

    # Filter 1: abstract_tr non-empty
    mask = df["abstract_tr"].str.len() > 0
    drops["empty_abstract"] = int((~mask).sum())
    df = df[mask].reset_index(drop=True)

    # Filter 2: abstract_tr >= MIN_WORDS
    word_counts = df["abstract_tr"].apply(_wc)
    mask = word_counts >= MIN_WORDS
    drops["short_abstract"] = int((~mask).sum())
    df = df[mask].reset_index(drop=True)

    # Filter 3: title_tr non-empty
    mask = df["title_tr"].str.len() > 0
    drops["empty_title"] = int((~mask).sum())
    df = df[mask].reset_index(drop=True)

    # Filter 4: dedupe by tez_no
    before = len(df)
    df = df.drop_duplicates(subset=["tez_no"], keep="first").reset_index(drop=True)
    drops["duplicate_tez_no"] = before - len(df)

    final = len(df)

    # Year distribution + subject diversity (for sanity)
    year_dist = df["year"].value_counts().sort_index().to_dict()
    subj_top = df["subject"].value_counts().head(20).to_dict()

    print(f"[+] Filter results:")
    print(f"    initial:     {initial:,}")
    for k, v in drops.items():
        print(f"    {k:18s} - {v:,}")
    print(f"    final:       {final:,}")

    df.to_parquet(DERIVED, index=False)
    print(f"[+] Wrote {DERIVED}")

    REPORT.write_text(
        json.dumps({
            "raw_path": str(RAW),
            "derived_path": str(DERIVED),
            "initial_rows": initial,
            "final_rows": final,
            "drops": drops,
            "min_words": MIN_WORDS,
            "year_min": int(min(year_dist) if year_dist else 0),
            "year_max": int(max(year_dist) if year_dist else 0),
            "year_distribution": {str(k): int(v) for k, v in year_dist.items()},
            "top_20_subjects": subj_top,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[+] Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
