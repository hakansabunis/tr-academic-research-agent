"""Build the Stage 2a continued pre-training corpus for trakad-7b-base.

Pipeline:
  1. Load YOK Tez (633K) + DergiPark (106K) filtered parquets.
  2. Quality filter (>=200-char abstract, >=5-char title).
  3. Cross-source dedup on tez_no.
  4. Format each doc as `{title}\n\n{abstract}`.
  5. Tokenize with Trendyol-LLM-7b-base-v1.0 SentencePiece tokenizer.
  6. Greedy atomic packing into max_seq_len=2048 chunks, separated by EOS.
  7. Save train/val parquet (99/1 split) with input_ids column.

Why these choices:
  - max_seq_len=2048: fits ~5-7 academic abstracts per chunk; A100 40GB
    with bf16 + gradient checkpointing handles micro_batch=1 comfortably.
  - Greedy atomic packing: each abstract stays whole (no mid-sentence
    splits); padding waste essentially zero; doc boundaries respected.
  - EOS-only separator (no attention-mask gating): standard HF/torch
    pattern, model learns boundaries via EOS, no extra engineering.
  - 99/1 train/val: ~2-3M validation tokens enough for PPL monitoring.

Usage:
    python models/writer/build_pretrain_corpus.py
    python models/writer/build_pretrain_corpus.py --smoke      # 5K docs
    python models/writer/build_pretrain_corpus.py --max-seq 4096
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

# Load .env so DATA_DIR resolves the same way the rest of the project does
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def _resolve_yok_path() -> Path:
    """YOK Tez filtered parquet sometimes lives in the project under
    data/derived/, sometimes in the external DATA_DIR (.env). Try both."""
    import os
    candidates: list[Path] = []
    if env_dir := os.getenv("DATA_DIR"):
        candidates.append(Path(env_dir) / "abstracts_filtered.parquet")
    candidates.append(ROOT / "data" / "derived" / "abstracts_filtered.parquet")
    for c in candidates:
        if c.exists():
            return c
    # Return the project-relative default for an informative error message
    return ROOT / "data" / "derived" / "abstracts_filtered.parquet"


DEFAULT_YOK = _resolve_yok_path()
DEFAULT_DERGIPARK = ROOT / "data" / "derived" / "dergipark_filtered.parquet"
DEFAULT_OUT = ROOT / "data" / "stage2a_corpus"

DEFAULT_BASE_MODEL = "Trendyol/Trendyol-LLM-7b-base-v1.0"
DEFAULT_MAX_SEQ = 2048
MIN_ABSTRACT_CHARS = 200
MIN_TITLE_CHARS = 5
SEED = 42
VAL_RATIO = 0.01


def load_source(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        print(f"[!] Missing {path}", file=sys.stderr)
        return pd.DataFrame()
    df = pd.read_parquet(path, columns=["tez_no", "title_tr", "abstract_tr"])
    print(f"[+] {label}: {len(df):,} raw rows")

    df["title_tr"] = df["title_tr"].fillna("").astype(str).str.strip()
    df["abstract_tr"] = df["abstract_tr"].fillna("").astype(str).str.strip()
    df["tez_no"] = df["tez_no"].astype(str)

    mask = (
        (df["title_tr"].str.len() >= MIN_TITLE_CHARS)
        & (df["abstract_tr"].str.len() >= MIN_ABSTRACT_CHARS)
    )
    df = df[mask].reset_index(drop=True)
    df["source"] = label
    print(f"    after quality filter: {len(df):,}")
    return df


def format_doc(title: str, abstract: str) -> str:
    """`{title}\\n\\n{abstract}` — natural academic flow."""
    return f"{title}\n\n{abstract}"


def pack_greedy(docs_tokens: list[list[int]], max_seq: int, eos_id: int) -> list[list[int]]:
    """Greedy atomic packing: each doc stays whole, EOS separates docs in a
    chunk. A doc that alone exceeds max_seq gets truncated."""
    chunks: list[list[int]] = []
    cur: list[int] = []
    dropped_truncated = 0
    for tok in docs_tokens:
        body = tok + [eos_id]
        if len(body) > max_seq:
            # Long doc — truncate to max_seq (rare). Keep what fits.
            body = body[: max_seq - 1] + [eos_id]
            dropped_truncated += 1
        # Does it fit in current chunk?
        if cur and (len(cur) + len(body) > max_seq):
            chunks.append(cur)
            cur = body
        else:
            cur.extend(body)
    if cur:
        chunks.append(cur)
    return chunks, dropped_truncated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yok", type=Path, default=DEFAULT_YOK)
    parser.add_argument("--dergipark", type=Path, default=DEFAULT_DERGIPARK)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--max-seq", type=int, default=DEFAULT_MAX_SEQ)
    parser.add_argument("--smoke", action="store_true",
                        help="Limit to first 5K docs total for quick validation")
    parser.add_argument("--val-ratio", type=float, default=VAL_RATIO)
    args = parser.parse_args()

    # Lazy imports
    print(f"[+] Loading tokenizer: {args.base_model}")
    from transformers import LlamaTokenizer
    tok = LlamaTokenizer.from_pretrained(args.base_model)
    eos_id = tok.eos_token_id
    print(f"    vocab={tok.vocab_size}, eos_id={eos_id}, max_seq={args.max_seq}")

    # Load + filter + dedup
    yok = load_source(args.yok, "yok")
    dp = load_source(args.dergipark, "dergipark")

    print(f"\n[+] Combining sources")
    combined = pd.concat([yok, dp], ignore_index=True)
    print(f"    before dedup: {len(combined):,}")
    combined = combined.drop_duplicates(subset=["tez_no"], keep="first").reset_index(drop=True)
    print(f"    after tez_no dedup: {len(combined):,}")

    if args.smoke:
        combined = combined.head(5000).reset_index(drop=True)
        print(f"    SMOKE: limited to {len(combined):,} docs")

    # Format docs
    print(f"\n[+] Formatting docs as '{{title}}\\n\\n{{abstract}}'")
    texts = [
        format_doc(row.title_tr, row.abstract_tr)
        for row in combined.itertuples(index=False)
    ]
    print(f"    {len(texts):,} doc strings")

    # Tokenize in batches (fast in C++ via sentencepiece — single batch call
    # processes the whole list, but we chunk to show progress)
    print(f"\n[+] Tokenizing (batched, sentencepiece backend)")
    batch_size = 1000
    docs_tokens: list[list[int]] = []
    t0 = time.time()
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        # add_special_tokens=False — we add EOS ourselves during packing
        ids = tok(batch, add_special_tokens=False)["input_ids"]
        docs_tokens.extend(ids)
        if (i // batch_size) % 10 == 0:
            elapsed = time.time() - t0
            rate = (i + batch_size) / elapsed if elapsed > 0 else 0
            print(f"    {i+batch_size:>7,}/{len(texts):,}  {rate:.0f} docs/s")
    dt = time.time() - t0
    print(f"    Tokenized {len(docs_tokens):,} docs in {dt/60:.1f} min")

    total_tokens = sum(len(t) for t in docs_tokens)
    avg_tokens = total_tokens / len(docs_tokens)
    print(f"    Total tokens: {total_tokens:,}  (avg {avg_tokens:.0f}/doc)")

    # Pack
    print(f"\n[+] Packing greedy-atomic into chunks of max_seq={args.max_seq}")
    chunks, n_truncated = pack_greedy(docs_tokens, args.max_seq, eos_id)
    total_chunk_tokens = sum(len(c) for c in chunks)
    avg_chunk_len = total_chunk_tokens / len(chunks)
    fill_ratio = total_chunk_tokens / (len(chunks) * args.max_seq)
    print(f"    {len(chunks):,} chunks, avg len {avg_chunk_len:.0f}, fill ratio {fill_ratio*100:.1f}%")
    if n_truncated:
        print(f"    {n_truncated} long docs were truncated to fit max_seq")

    # 99/1 train/val split (seeded)
    rng = random.Random(SEED)
    indices = list(range(len(chunks)))
    rng.shuffle(indices)
    n_val = max(1, int(len(chunks) * args.val_ratio))
    val_idx = set(indices[:n_val])
    train_chunks = [chunks[i] for i in range(len(chunks)) if i not in val_idx]
    val_chunks = [chunks[i] for i in range(len(chunks)) if i in val_idx]
    print(f"\n[+] Train/val split: {len(train_chunks):,} / {len(val_chunks):,}")

    # Save
    args.out_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.out_dir / "train.parquet"
    val_path = args.out_dir / "val.parquet"
    stats_path = args.out_dir / "_corpus_stats.json"

    train_df = pd.DataFrame({"input_ids": train_chunks})
    val_df = pd.DataFrame({"input_ids": val_chunks})
    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)

    stats = {
        "base_model": args.base_model,
        "max_seq": args.max_seq,
        "n_docs_input": int(len(combined)),
        "n_docs_yok": int((combined["source"] == "yok").sum()),
        "n_docs_dergipark": int((combined["source"] == "dergipark").sum()),
        "total_tokens": int(total_tokens),
        "avg_tokens_per_doc": round(avg_tokens, 1),
        "n_chunks": int(len(chunks)),
        "n_train_chunks": int(len(train_chunks)),
        "n_val_chunks": int(len(val_chunks)),
        "total_chunk_tokens": int(total_chunk_tokens),
        "fill_ratio": round(fill_ratio, 4),
        "n_truncated_docs": int(n_truncated),
        "elapsed_tokenize_min": round(dt / 60, 2),
        "smoke": bool(args.smoke),
    }
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[+] Wrote:")
    print(f"    {train_path}  ({train_path.stat().st_size/1024/1024:.1f} MB)")
    print(f"    {val_path}    ({val_path.stat().st_size/1024/1024:.1f} MB)")
    print(f"    {stats_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
