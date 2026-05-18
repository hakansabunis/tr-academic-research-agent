"""Push the Turkish HF cards (README.md) to the model + dataset repos.

Token from .env (HF_TOKEN). Idempotent.

    python scripts/35_push_hf_cards.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from huggingface_hub import HfApi  # noqa: E402

CARDS = [
    (ROOT / "docs" / "hf" / "model_card_trakad_embed_v2.md",
     "hakansabunis/trakad-embed-v2", "model"),
    (ROOT / "docs" / "hf" / "dataset_card_index.md",
     "hakansabunis/tr-academic-research-agent-index", "dataset"),
]


def main() -> int:
    tok = os.getenv("HF_TOKEN")
    if not tok:
        print("[!] HF_TOKEN missing in .env", file=sys.stderr)
        return 2
    api = HfApi(token=tok)
    for path, repo, rtype in CARDS:
        if not path.exists():
            print(f"[!] missing {path}", file=sys.stderr)
            return 1
        print(f"[+] {path.name} -> {rtype}:{repo}/README.md")
        api.upload_file(
            path_or_fileobj=str(path),
            path_in_repo="README.md",
            repo_id=repo,
            repo_type=rtype,
            commit_message="Turkish card: usage + cross-links",
        )
    print("\n[+] Cards updated:")
    print("  https://huggingface.co/hakansabunis/trakad-embed-v2")
    print("  https://huggingface.co/datasets/hakansabunis/tr-academic-research-agent-index")
    print("  (Space card already deployed via scripts/34_deploy_space.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
