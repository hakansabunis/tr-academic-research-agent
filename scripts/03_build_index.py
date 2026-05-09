"""Build the Chroma vector index from the filtered parquet.

Design choices:
  - id        = str(tez_no)                 (joinable back to parquet)
  - document  = title_tr + "\\n\\n" + abstract_tr   (lexical signal + content)
  - metadata  = full thesis metadata for citation + filtering
  - distance  = cosine                       (HNSW: hnsw:space=cosine)
  - embedder  = paraphrase-multilingual-mpnet-base-v2  (768-dim)

Staged execution — pass --limit to embed only the first N rows. Recommended
ladder for the RTX 3050 Ti (4 GB VRAM):
   --limit 1000     (smoke,    ~2 min)
   --limit 50000    (mid eval, ~1 hour)
   (no --limit)     (full,     ~8-14 hours, run overnight)

The script is **resumable**: if the collection already has K records, it
starts from row K. Safe to interrupt and re-run.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PARQUET = ROOT / "data" / "derived" / "abstracts_filtered.parquet"
DEFAULT_PERSIST = ROOT / "data" / "chroma_db"
DEFAULT_COLLECTION = "turkish_theses"
DEFAULT_EMBED = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


def _row_doc(row: pd.Series) -> str:
    title = (row.get("title_tr") or "").strip()
    abstract = (row.get("abstract_tr") or "").strip()
    if title:
        return f"{title}\n\n{abstract}"
    return abstract


def _row_meta(row: pd.Series) -> dict:
    def s(k: str) -> str:
        v = row.get(k)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        return str(v)

    year = row.get("year")
    try:
        year_int = int(year) if year is not None and not pd.isna(year) else 0
    except (TypeError, ValueError):
        year_int = 0

    return {
        "tez_no": s("tez_no"),
        "title_tr": s("title_tr"),
        "title_en": s("title_en"),
        "author": s("author"),
        "advisor": s("advisor"),
        "location": s("location"),
        "subject": s("subject"),
        "year": year_int,
        "pages": int(row.get("pages") or 0) if not pd.isna(row.get("pages") or 0) else 0,
        "degree": s("degree"),
        "pdf_url": s("pdf_url"),
        "language": s("language"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--persist-dir", type=Path, default=DEFAULT_PERSIST)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--embed-model", default=DEFAULT_EMBED)
    parser.add_argument("--limit", type=int, default=None,
                        help="Index only first N rows (smoke / staged runs)")
    parser.add_argument("--batch", type=int, default=128)
    args = parser.parse_args()

    if not args.parquet.exists():
        print(f"[!] Missing {args.parquet}. Run scripts/02_filter_data.py first.", file=sys.stderr)
        return 1

    import chromadb
    from chromadb.utils import embedding_functions

    print(f"[+] Loading parquet: {args.parquet}")
    df = pd.read_parquet(args.parquet)
    print(f"[+] {len(df):,} rows")

    if args.limit is not None:
        df = df.head(args.limit).reset_index(drop=True)
        print(f"[+] Limiting to first {len(df):,} rows")

    args.persist_dir.mkdir(parents=True, exist_ok=True)
    print(f"[+] Chroma persist dir: {args.persist_dir}")
    client = chromadb.PersistentClient(path=str(args.persist_dir))

    print(f"[+] Loading embedder: {args.embed_model}")
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=args.embed_model)

    coll = client.get_or_create_collection(
        name=args.collection,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    existing = coll.count()
    print(f"[+] Collection '{args.collection}' has {existing:,} existing records")

    if existing >= len(df):
        print("[=] Index already covers the requested range — nothing to do.")
        return 0

    df = df.iloc[existing:].reset_index(drop=True)
    print(f"[+] Resuming: indexing {len(df):,} more rows from row {existing:,}")

    t0 = time.time()
    indexed = 0
    for i in tqdm(range(0, len(df), args.batch), desc="indexing"):
        batch = df.iloc[i : i + args.batch]
        ids = [str(t) for t in batch["tez_no"].tolist()]
        docs = [_row_doc(r) for _, r in batch.iterrows()]
        metas = [_row_meta(r) for _, r in batch.iterrows()]
        coll.upsert(ids=ids, documents=docs, metadatas=metas)
        indexed += len(batch)

    dt = time.time() - t0
    final = coll.count()
    print(f"[+] Done. Added {indexed:,} rows in {dt/60:.1f} min. Collection now {final:,} records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
