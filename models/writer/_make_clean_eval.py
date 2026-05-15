"""Build a FAIR evaluation set: raw clean Turkish academic abstract text.

Unlike pretrain_corpus/val.parquet (packed token chunks → decode-repack
artefact penalized our model), this is plain text. Each model tokenizes
it with its OWN tokenizer at eval time → fair cross-model BPC.

Sampling: 2000 clean abstracts, held out from the training distribution
by SEED offset (different sample than what trained).

Output: data/derived/clean_eval.parquet  (columns: text)
Pushes to HF Hub: tr-academic-research-agent-index/pretrain_corpus/clean_eval.parquet
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

YOK = ROOT / "data" / "derived" / "abstracts_filtered_clean.parquet"
DP = ROOT / "data" / "derived" / "dergipark_filtered_clean.parquet"
OUT = ROOT / "data" / "derived" / "clean_eval.parquet"

N_SAMPLE = 2000
SEED = 1234  # different seed than corpus build (SEED=42) → held-out flavour


def main() -> int:
    if not YOK.exists() or not DP.exists():
        print("[!] Run clean_corpus.py first", file=sys.stderr)
        return 1

    yok = pd.read_parquet(YOK, columns=["tez_no", "title_tr", "abstract_tr"])
    dp = pd.read_parquet(DP, columns=["tez_no", "title_tr", "abstract_tr"])
    yok["source"] = "yok"
    dp["source"] = "dergipark"
    df = pd.concat([yok, dp], ignore_index=True)
    print(f"[+] Combined clean pool: {len(df):,}")

    # Same doc format as training: "{title}\n\n{abstract}"
    df["title_tr"] = df["title_tr"].fillna("").astype(str).str.strip()
    df["abstract_tr"] = df["abstract_tr"].fillna("").astype(str).str.strip()
    df = df[(df["title_tr"].str.len() >= 5) & (df["abstract_tr"].str.len() >= 200)]
    df["text"] = df["title_tr"] + "\n\n" + df["abstract_tr"]

    sample = df.sample(n=min(N_SAMPLE, len(df)), random_state=SEED).reset_index(drop=True)
    out_df = sample[["tez_no", "source", "text"]].copy()
    out_df["tez_no"] = out_df["tez_no"].astype(str)  # mixed int/str -> str
    out_df.to_parquet(OUT, index=False)
    print(f"[+] Wrote {OUT} ({len(out_df):,} rows)")
    print(f"    avg text chars: {out_df['text'].str.len().mean():.0f}")
    print(f"    source mix: {out_df['source'].value_counts().to_dict()}")

    # Push to HF Hub
    token = os.getenv("HF_TOKEN")
    if not token:
        print("\n[!] HF_TOKEN not set — skipping Hub push. "
              "Set it and re-run, or push manually.", file=sys.stderr)
        return 0
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="pretrain_corpus/clean_eval.parquet",
        repo_id="hakansabunis/tr-academic-research-agent-index",
        repo_type="dataset",
        commit_message="Add fair clean-text eval set (2000 raw clean abstracts, per-model tokenization)",
        token=token,
    )
    print("[+] Pushed to HF Hub: pretrain_corpus/clean_eval.parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
