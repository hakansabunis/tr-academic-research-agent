"""D5a — Size probe for a free hosted vector DB (Qdrant/Chroma Cloud).

Decides WHETHER the 633K v2 index can fit a ~1GB free tier, and under
which config. The bottleneck is usually the abstract *payload*, not the
vectors. We sample to estimate, then project full-corpus sizes under:

  vectors:  float32 | int8 (scalar quant) | binary (1-bit)
  payload:  full abstract | abstract truncated to N chars | tez_no-only
            (abstracts fetched separately by tez_no at query time)

No API, no writes — read-only probe of the local chroma_db_v2.

Usage:
    python scripts/30_index_size_probe.py
    python scripts/30_index_size_probe.py --sample 8000 --trunc 800
"""
from __future__ import annotations

import argparse
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from turk_researcher.config import load_settings  # noqa: E402


def _h(n: float) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=6000)
    ap.add_argument("--trunc", type=int, default=800,
                    help="Truncated-abstract scenario: chars kept")
    args = ap.parse_args()

    import chromadb

    s = load_settings()
    print(f"[i] collection dir: {s.chroma_persist_dir}")
    client = chromadb.PersistentClient(path=str(s.chroma_persist_dir))
    coll = client.get_collection(name=s.chroma_collection)
    total = coll.count()
    print(f"[i] total vectors: {total:,}")

    n = min(args.sample, total)
    got = coll.get(limit=n, include=["embeddings", "documents", "metadatas"])
    embs = got["embeddings"]
    embs = [] if embs is None else list(embs)
    docs = got["documents"] or []
    metas = got["metadatas"] or []
    dim = len(embs[0]) if len(embs) else 0
    print(f"[i] sampled {len(embs):,} · embedding dim = {dim}")

    doc_lens = [len(d or "") for d in docs]
    # Minimal payload kept in the DB even in the "tez_no-only" scenario:
    # tez_no + title + year ≈ enough to render a citation; abstract fetched
    # externally by tez_no.
    meta_min = [len(str(m.get("tez_no", ""))) + len(str(m.get("title_tr", "")))
                + 8 for m in metas]
    avg_doc = st.mean(doc_lens) if doc_lens else 0
    avg_min = st.mean(meta_min) if meta_min else 0
    print(f"[i] avg abstract chars = {avg_doc:.0f} "
          f"(p50={st.median(doc_lens):.0f}, max={max(doc_lens)}) · "
          f"avg min-meta = {avg_min:.0f}")

    # Per-vector byte models (UTF-8 Turkish ~1.05 B/char; payload + index
    # overhead fudge ×1.25 for HNSW/json keys).
    OVH = 1.25
    vec = {
        "float32": dim * 4,
        "int8 (scalar)": dim * 1,
        "binary (1-bit)": dim / 8,
    }
    pay = {
        "full abstract": avg_doc * 1.05 + avg_min,
        f"abstract≤{args.trunc}c": min(avg_doc, args.trunc) * 1.05 + avg_min,
        "tez_no+title only": avg_min,
    }

    print("\nProjected FULL-corpus size (n=%s, ×%.2f overhead):" % (f"{total:,}", OVH))
    print(f"{'vectors / payload':<22}" + "".join(f"{p:>20}" for p in pay))
    fits = []
    for vname, vb in vec.items():
        row = f"{vname:<22}"
        for pname, pb in pay.items():
            tot = (vb + pb) * total * OVH
            row += f"{_h(tot):>20}"
            if tot < 1024 ** 3:  # < 1 GB free-tier rule of thumb
                fits.append((vname, pname, tot))
        print(row)

    print("\n[verdict]")
    if fits:
        print("  Fits a ~1GB free tier under:")
        for v, p, t in sorted(fits, key=lambda x: x[2]):
            print(f"   - {v} + {p}  →  {_h(t)}")
        print("  → Recommended: best retrieval quality that still fits "
              "(prefer int8 over binary; truncated abstract over tez_no-only "
              "since the reranker needs abstract text).")
    else:
        print("  Nothing fits ~1GB. Options: tez_no-only payload + abstracts "
              "served from the HF parquet by tez_no, or a corpus subset, or "
              "a 2GB+ free tier.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
