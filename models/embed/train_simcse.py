"""Fine-tune mpnet-base-v2 on Turkish academic theses with
MultipleNegativesRankingLoss + subject-aware hard negatives.

Output: a sentence-transformers model directory (`trakad-embed-v2/`) and
optionally a Hugging Face Hub push.

Why this recipe (vs unsupervised SimCSE we tried before):
- title↔abstract pairs give a strong, label-free supervision signal that
  the previous unsupervised dropout-augmentation attempt lacked.
- A single explicit hard negative per anchor (same subject, different
  thesis) plus the in-batch negatives from MultipleNegativesRankingLoss
  prevents the representational collapse seen in the prior run.
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRIPLETS = ROOT / "data" / "derived" / "embed_training_triplets.parquet"
DEFAULT_OUT = ROOT / "models" / "embed" / "trakad-embed-v2"

DEFAULT_BASE_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--triplets", type=Path, default=DEFAULT_TRIPLETS,
                        help="Path to training triplet parquet")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT,
                        help="Where to save the fine-tuned model")
    parser.add_argument("--batch-size", type=int, default=64,
                        help="Per-device train batch (T4 16 GB handles 64 with mpnet)")
    parser.add_argument("--epochs", type=int, default=1,
                        help="One epoch is usually plenty for domain fine-tune")
    parser.add_argument("--lr", type=float, default=2e-5,
                        help="Low LR avoids catastrophic forgetting of pre-trained knowledge")
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--max-seq-length", type=int, default=256,
                        help="Most thesis abstracts fit; 512 is overkill and slow")
    parser.add_argument("--eval-every", type=int, default=2000,
                        help="Print loss / sample similarity every N steps")
    parser.add_argument("--push-to-hub", default=None,
                        help="If set, upload to this HF Hub repo (e.g. hakansabunis/trakad-embed-v2)")
    parser.add_argument("--hub-token", default=None,
                        help="HF write token (or set HF_TOKEN env var)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Use only first N triplets (smoke test)")
    args = parser.parse_args()

    # Lazy imports — keeps argparse fast and avoids importing torch on --help
    import torch
    from sentence_transformers import (
        SentenceTransformer, InputExample, losses, models,
    )
    from torch.utils.data import DataLoader

    if not args.triplets.exists():
        print(f"[!] Triplets parquet missing: {args.triplets}", file=sys.stderr)
        print(f"    Run build_training_pairs.py first.", file=sys.stderr)
        return 1

    print(f"[+] Reading triplets: {args.triplets}")
    df = pd.read_parquet(args.triplets)
    print(f"    {len(df):,} triplets")
    if args.limit:
        df = df.head(args.limit).reset_index(drop=True)
        print(f"    limited to first {len(df):,} (smoke)")

    # Build sentence-transformers training examples
    print("[+] Constructing InputExample list...")
    train_examples = [
        InputExample(texts=[row.anchor, row.positive, row.hard_negative])
        for row in df.itertuples(index=False)
    ]
    print(f"    {len(train_examples):,} examples ready")

    # Model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[+] Loading base model: {args.base_model}  (device={device})")
    model = SentenceTransformer(args.base_model, device=device)
    model.max_seq_length = args.max_seq_length

    # Loss
    loss = losses.MultipleNegativesRankingLoss(model)

    # Loader
    loader = DataLoader(
        train_examples,
        shuffle=True,
        batch_size=args.batch_size,
        num_workers=2,
    )

    steps_per_epoch = math.ceil(len(train_examples) / args.batch_size)
    total_steps = steps_per_epoch * args.epochs
    warmup_steps = int(total_steps * args.warmup_ratio)

    print(f"[+] Training plan: {args.epochs} epoch(s) × {steps_per_epoch} step(s) = {total_steps:,}")
    print(f"    Warmup: {warmup_steps} steps ({args.warmup_ratio*100:.1f}%)")
    print(f"    LR: {args.lr}, batch: {args.batch_size}, max_seq: {args.max_seq_length}")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    model.fit(
        train_objectives=[(loader, loss)],
        epochs=args.epochs,
        warmup_steps=warmup_steps,
        optimizer_params={"lr": args.lr},
        output_path=str(args.output),
        show_progress_bar=True,
        save_best_model=False,
    )
    dt = time.time() - t0
    print(f"[+] Training done in {dt/60:.1f} min")
    print(f"    Saved to: {args.output}")

    # Optional Hub push
    if args.push_to_hub:
        from huggingface_hub import HfApi, login
        token = args.hub_token or _env_token()
        if not token:
            print("[!] Hub push requested but no token (--hub-token or HF_TOKEN)", file=sys.stderr)
            return 2
        login(token=token, add_to_git_credential=False)
        print(f"[+] Pushing to Hugging Face Hub: {args.push_to_hub}")
        api = HfApi(token=token)
        api.create_repo(args.push_to_hub, repo_type="model", exist_ok=True, token=token)
        api.upload_folder(
            folder_path=str(args.output),
            repo_id=args.push_to_hub,
            repo_type="model",
            commit_message="trakad-embed-v2 — Turkish academic SimCSE fine-tune of mpnet-base-v2",
            token=token,
        )
        print(f"[+] Pushed: https://huggingface.co/{args.push_to_hub}")

    return 0


def _env_token() -> str | None:
    import os
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")


if __name__ == "__main__":
    raise SystemExit(main())
