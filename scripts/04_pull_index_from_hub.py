"""Pull the prebuilt Chroma index + filtered parquet from Hugging Face Hub.

Use this AFTER running `colab/build_index_colab.ipynb` on Colab GPU and
uploading the artifacts to HF Hub. Downloads them to DATA_DIR (set via .env)
so the LangGraph agents can run against them without GPU.

Usage:
    python scripts/04_pull_index_from_hub.py
    python scripts/04_pull_index_from_hub.py --repo hakansabunis/tr-academic-research-agent-index
    python scripts/04_pull_index_from_hub.py --data-dir C:\\dev\\turk-researcher-data
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Add src to path so we can import config (which respects DATA_DIR env var)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from turk_researcher.config import load_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=None,
                        help="HF dataset repo id (default: from HF_INDEX_REPO env)")
    parser.add_argument("--data-dir", type=Path, default=None,
                        help="Override DATA_DIR (default: from .env)")
    parser.add_argument("--variant", default="v1", choices=["v1", "v2"],
                        help="v1 = chroma_db/ (mpnet baseline), v2 = chroma_db_v2/ (trakad-embed-v2)")
    parser.add_argument("--token", default=None,
                        help="HF token if the dataset is private (or set HF_TOKEN env var)")
    parser.add_argument("--force", action="store_true",
                        help="Re-download even if local copies exist")
    args = parser.parse_args()

    settings = load_settings()
    repo = args.repo or settings.hf_index_repo
    data_dir = args.data_dir or settings.data_dir
    # v1 -> chroma_db (existing layout), v2 -> chroma_db_v2 (new layout)
    chroma_subdir = "chroma_db" if args.variant == "v1" else "chroma_db_v2"
    chroma_dir = data_dir / chroma_subdir
    parquet_path = data_dir / "abstracts_filtered.parquet"
    report_path = data_dir / "filter_report.json"

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("[!] huggingface_hub missing. Run: pip install -r requirements.txt", file=sys.stderr)
        return 1

    if not args.force and chroma_dir.exists() and parquet_path.exists():
        print(f"[=] Already present: {chroma_dir}, {parquet_path} — skipping (use --force to re-download).")
        return 0

    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"[+] Pulling {repo} from Hugging Face Hub  (variant={args.variant})")
    print(f"    target: {data_dir}")
    print("    (~14-16 GB total — first pull can take 15-30 minutes depending on bandwidth)")

    cache = data_dir / "_hub_cache"
    cache.mkdir(parents=True, exist_ok=True)

    # Only download the requested variant's chroma folder + parquet/report,
    # not both v1 and v2 (would be 30+ GB).
    allow = [
        f"{chroma_subdir}/*",
        "abstracts_filtered.parquet",
        "filter_report.json",
    ]

    snapshot_download(
        repo_id=repo,
        repo_type="dataset",
        local_dir=str(cache),
        allow_patterns=allow,
        token=args.token,
    )

    chroma_src = cache / chroma_subdir
    parquet_src = cache / "abstracts_filtered.parquet"
    report_src = cache / "filter_report.json"

    if not chroma_src.exists():
        print(f"[!] Expected {chroma_subdir}/ in {cache} — repo layout mismatch", file=sys.stderr)
        return 2

    if chroma_dir.exists() and args.force:
        print(f"[+] Removing existing {chroma_dir}")
        shutil.rmtree(chroma_dir)

    print(f"[+] Moving {chroma_subdir} -> {chroma_dir}")
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
    shutil.move(str(chroma_src), str(chroma_dir))

    if parquet_src.exists():
        print(f"[+] Moving abstracts_filtered.parquet -> {parquet_path}")
        if parquet_path.exists():
            parquet_path.unlink()
        shutil.move(str(parquet_src), str(parquet_path))

    if report_src.exists():
        print(f"[+] Moving filter_report.json -> {report_path}")
        if report_path.exists():
            report_path.unlink()
        shutil.move(str(report_src), str(report_path))

    if cache.exists():
        shutil.rmtree(cache, ignore_errors=True)

    chroma_size_gb = sum(
        f.stat().st_size for f in chroma_dir.rglob("*") if f.is_file()
    ) / 1024 ** 3

    print(f"\n[+] Done. Chroma DB: {chroma_size_gb:.1f} GB at {chroma_dir}")
    print("    You can now run the agent:")
    print('    python scripts/run.py "Türkçe doğal dil işleme yöntemleri nelerdir?"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
