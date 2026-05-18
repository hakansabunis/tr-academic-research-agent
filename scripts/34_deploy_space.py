"""D2.3b — Deploy the real-system app to the HF Space.

Pushes space/{app.py,requirements.txt,README.md} to the Space repo so it
rebuilds with the memory-backend pipeline. Run AFTER 33_push_memstore_hf.py
(the Space pulls those artifacts at boot).

Token from .env (HF_TOKEN). Space repo defaults to the canonical one.

Usage:
    python scripts/34_deploy_space.py
    python scripts/34_deploy_space.py --space hakansabunis/turkresearcher
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from huggingface_hub import HfApi  # noqa: E402

SPACE_DIR = ROOT / "space"
FILES = ["app.py", "requirements.txt", "README.md"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--space", default="hakansabunis/turkresearcher")
    args = ap.parse_args()

    tok = os.getenv("HF_TOKEN")
    if not tok:
        print("[!] HF_TOKEN missing in .env", file=sys.stderr)
        return 2

    api = HfApi(token=tok)
    # Ensure the Space exists (gradio sdk). Idempotent.
    api.create_repo(repo_id=args.space, repo_type="space", space_sdk="gradio",
                    exist_ok=True)

    for fn in FILES:
        p = SPACE_DIR / fn
        if not p.exists():
            print(f"[!] missing {p}", file=sys.stderr)
            return 1
        print(f"[+] uploading space/{fn} -> {args.space}")
        api.upload_file(
            path_or_fileobj=str(p),
            path_in_repo=fn,
            repo_id=args.space,
            repo_type="space",
            commit_message="Deploy real-system app (memory backend + reranker)",
        )

    # The Space is a separate repo — it needs the turk_researcher package.
    # Ship src/turk_researcher → /app/src/turk_researcher (app.py adds
    # APP_DIR/src to sys.path).
    src = ROOT / "src" / "turk_researcher"
    print(f"[+] uploading src/turk_researcher/ -> {args.space}:src/turk_researcher/")
    api.upload_folder(
        folder_path=str(src),
        path_in_repo="src/turk_researcher",
        repo_id=args.space,
        repo_type="space",
        allow_patterns=["**/*.py"],
        ignore_patterns=["**/__pycache__/**"],
        commit_message="Ship turk_researcher package to Space",
    )

    print(f"\n[+] Deployed. Space rebuilding: "
          f"https://huggingface.co/spaces/{args.space}")
    print("    First boot pulls ~2 GB artifacts + warms index — give it a few min.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
