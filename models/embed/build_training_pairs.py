"""Build (anchor, positive, hard_negative) triplets for SimCSE-style training.

For every filtered Turkish thesis:
  anchor          = title_tr
  positive        = abstract_tr
  hard_negative   = abstract_tr from a *different* thesis in the *same*
                    subject area (when available, else a random thesis)

Why these choices:
- title↔abstract is a natural in-document pair: same content, two abstraction
  levels. Excellent positive signal without any human annotation.
- Same-subject hard negatives force the model to discriminate within a
  topical cluster (e.g. distinguishing two CS theses on different methods),
  which is exactly the failure mode we observed in the 30-question eval.

Output: data/derived/embed_training_triplets.parquet  (3 string columns)
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "derived" / "abstracts_filtered.parquet"
DEFAULT_OUTPUT = ROOT / "data" / "derived" / "embed_training_triplets.parquet"

MIN_ABSTRACT_CHARS = 200   # quality floor (already filtered to ≥50 words upstream)
MIN_TITLE_CHARS = 5        # avoid trivially short titles
SEED = 42


def build(parquet_path: Path, n_sample: int | None = None) -> pd.DataFrame:
    if not parquet_path.exists():
        raise FileNotFoundError(f"Filtered parquet not found: {parquet_path}")

    print(f"[+] Reading {parquet_path}")
    df = pd.read_parquet(parquet_path, columns=["tez_no", "title_tr", "abstract_tr", "subject"])
    print(f"    {len(df):,} rows")

    if n_sample is not None and n_sample < len(df):
        df = df.sample(n=n_sample, random_state=SEED).reset_index(drop=True)
        print(f"    sampled to {len(df):,} rows")

    # Quality cleanup
    df["title_tr"] = df["title_tr"].fillna("").astype(str).str.strip()
    df["abstract_tr"] = df["abstract_tr"].fillna("").astype(str).str.strip()
    df["subject"] = df["subject"].fillna("_unknown_").astype(str)

    mask = (
        (df["title_tr"].str.len() >= MIN_TITLE_CHARS)
        & (df["abstract_tr"].str.len() >= MIN_ABSTRACT_CHARS)
    )
    dropped = (~mask).sum()
    if dropped:
        print(f"    drop {dropped:,} rows with empty/short title or abstract")
    df = df[mask].reset_index(drop=True)

    # Index by subject for O(1) hard-negative sampling
    by_subject: dict[str, list[int]] = defaultdict(list)
    for idx, subj in enumerate(df["subject"].values):
        by_subject[subj].append(idx)

    rng = random.Random(SEED)
    all_indices = list(range(len(df)))

    triplets = {"anchor": [], "positive": [], "hard_negative": []}
    same_subject_hits = 0
    fallback_random = 0

    for idx in range(len(df)):
        anchor = df.iat[idx, df.columns.get_loc("title_tr")]
        positive = df.iat[idx, df.columns.get_loc("abstract_tr")]
        subj = df.iat[idx, df.columns.get_loc("subject")]

        # Same-subject hard negative
        candidates = by_subject[subj]
        if len(candidates) > 1:
            for _ in range(5):  # at most 5 retries to find a different one
                neg_idx = rng.choice(candidates)
                if neg_idx != idx:
                    break
            same_subject_hits += 1
        else:
            # Fallback: random thesis (different subject)
            for _ in range(5):
                neg_idx = rng.choice(all_indices)
                if neg_idx != idx:
                    break
            fallback_random += 1

        hard_neg = df.iat[neg_idx, df.columns.get_loc("abstract_tr")]
        triplets["anchor"].append(anchor)
        triplets["positive"].append(positive)
        triplets["hard_negative"].append(hard_neg)

    print(f"[+] Built {len(triplets['anchor']):,} triplets")
    print(f"    same-subject hard neg : {same_subject_hits:,}")
    print(f"    random fallback       : {fallback_random:,}")
    return pd.DataFrame(triplets)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                        help="Filtered thesis parquet")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Where to write the triplet parquet")
    parser.add_argument("--sample", type=int, default=None,
                        help="If set, sample this many rows (smoke test)")
    args = parser.parse_args()

    out_df = build(args.input, n_sample=args.sample)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(args.output, index=False)
    size_mb = args.output.stat().st_size / 1024 / 1024
    print(f"[+] Wrote {args.output}  ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
