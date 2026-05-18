"""D2.3a — Push the memory-store artifacts to the HF index dataset.

Uploads under `memstore/` in hakansabunis/tr-academic-research-agent-index
so the free HF Space can pull them at startup (no external DB):

    memstore/vectors_uint8.npy            (~464 MB)  uint8 633K×768
    memstore/payload.parquet              (~92 MB)   minimal citation meta
    memstore/abstracts_filtered_clean.parquet (~1.5 GB) tez_no→abstract

Token from .env (HF_TOKEN). Idempotent: re-runs overwrite.

Usage:
    python scripts/33_push_memstore_hf.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(ROOT / ".env")

from huggingface_hub import HfApi  # noqa: E402
from turk_researcher.config import load_settings  # noqa: E402

FILES = [
    (ROOT / "data" / "derived" / "qdrant_export" / "vectors_uint8.npy",
     "memstore/vectors_uint8.npy"),
    (ROOT / "data" / "derived" / "qdrant_export" / "payload.parquet",
     "memstore/payload.parquet"),
    (ROOT / "data" / "derived" / "abstracts_filtered_clean.parquet",
     "memstore/abstracts_filtered_clean.parquet"),
]


def main() -> int:
    tok = os.getenv("HF_TOKEN")
    if not tok:
        print("[!] HF_TOKEN missing in .env", file=sys.stderr)
        return 2
    repo = load_settings().hf_index_repo
    api = HfApi(token=tok)

    missing = [str(p) for p, _ in FILES if not p.exists()]
    if missing:
        print("[!] Missing artifacts:\n  " + "\n  ".join(missing), file=sys.stderr)
        return 1

    for path, dest in FILES:
        mb = path.stat().st_size / 1024 / 1024
        print(f"[+] uploading {path.name} -> {repo}:{dest}  ({mb:.0f} MB)")
        api.upload_file(
            path_or_fileobj=str(path),
            path_in_repo=dest,
            repo_id=repo,
            repo_type="dataset",
            commit_message=f"memstore: {dest}",
        )
        print(f"    done: {dest}")

    print(f"\n[+] All artifacts in https://huggingface.co/datasets/{repo}/tree/main/memstore")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
