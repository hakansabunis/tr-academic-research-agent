"""Push Stage 2a pre-train corpus to HF Hub.

Targets: hakansabunis/tr-academic-research-agent-index/pretrain_corpus/

Set HF_TOKEN env var, or pass --token.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / "data" / "stage2a_corpus"
DEFAULT_REPO = "hakansabunis/tr-academic-research-agent-index"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--token", default=None,
                        help="HF write token (or set HF_TOKEN env var)")
    args = parser.parse_args()

    token = args.token or os.getenv("HF_TOKEN")
    if not token:
        print("[!] No HF_TOKEN set. Pass --token or set HF_TOKEN env var.",
              file=sys.stderr)
        return 1

    if not args.dir.exists():
        print(f"[!] Missing corpus dir: {args.dir}", file=sys.stderr)
        return 2

    api = HfApi(token=token)

    # Files we want to push (train.parquet, val.parquet, _corpus_stats.json)
    api.upload_folder(
        folder_path=str(args.dir),
        path_in_repo="pretrain_corpus",
        repo_id=args.repo,
        repo_type="dataset",
        commit_message="Add Stage 2a pre-train corpus (740K docs, ~387M tokens, packed max_seq=2048)",
        token=token,
    )
    print(f"[+] Pushed -> https://huggingface.co/datasets/{args.repo}/tree/main/pretrain_corpus")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
