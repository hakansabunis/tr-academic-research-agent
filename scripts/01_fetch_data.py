"""Download the raw 650K Turkish thesis dataset from Hugging Face.

Source: umutertugrul/turkish-academic-theses-dataset (CC-BY-4.0).
Reproducibility: anyone cloning this repo can rebuild from scratch by running
this script — no dependency on a sibling project's local files.

Output: data/raw/abstracts_raw.parquet  (~1.56 GB)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RAW_PATH = RAW_DIR / "abstracts_raw.parquet"

HF_DATASET = "umutertugrul/turkish-academic-theses-dataset"


def main() -> int:
    if RAW_PATH.exists():
        size_mb = RAW_PATH.stat().st_size / 1024 / 1024
        print(f"[=] Already present: {RAW_PATH} ({size_mb:.1f} MB) — skipping.")
        print("    Delete it to force a re-download.")
        return 0

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[+] Downloading {HF_DATASET} from Hugging Face Hub")
    print("    (~1.56 GB — first run can take a few minutes)")

    try:
        from datasets import load_dataset
    except ImportError:
        print("[!] `datasets` package missing. Run: pip install -r requirements.txt", file=sys.stderr)
        return 1

    ds = load_dataset(HF_DATASET, split="train")
    print(f"[+] Loaded {len(ds):,} rows. Writing parquet -> {RAW_PATH}")
    ds.to_parquet(str(RAW_PATH))

    size_mb = RAW_PATH.stat().st_size / 1024 / 1024
    print(f"[+] Done. {size_mb:.1f} MB saved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
