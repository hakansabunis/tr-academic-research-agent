"""D5b.1 — Export the v2 index as a compact Qdrant-ready artifact.

Why uint8 *datatype* (not Qdrant's quantization-on-top): Qdrant always
keeps original float32 vectors when you use its scalar quantization, so a
quantized collection still costs ~1.9 GB for 633K×768 — over the free
tier. Storing the vectors *as* uint8 (Qdrant `datatype: uint8`) removes
the float32 originals entirely → ~580 MB vectors, fits.

Quality: embeddings are L2-normalized, then mapped [-1,1] → [0,255] per
component. Cosine on uint8 is a close approximation; the cross-encoder
reranker (kept, full abstract) recovers precision. Quality-preserving by
design — we do NOT truncate abstracts (abstracts are served separately by
tez_no from the existing parquet; see D5b.2).

Outputs (data/derived/qdrant_export/):
  vectors_uint8.npy   (N, 768) uint8
  payload.parquet     tez_no,title_tr,author,year,advisor,location,pdf_url
  meta.json           {count, dim, scheme, bytes...}

No API. Streams the collection in batches (bounded RAM).

Usage:
    python scripts/31_export_qdrant.py
    python scripts/31_export_qdrant.py --batch 20000 --limit 50000   # smoke
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from turk_researcher.config import load_settings  # noqa: E402

OUT = ROOT / "data" / "derived" / "qdrant_export"
PAYLOAD_KEYS = ("tez_no", "title_tr", "author", "year", "advisor",
                "location", "pdf_url")


def _quantize_uint8(vecs: np.ndarray) -> np.ndarray:
    """L2-normalize then map [-1,1] → [0,255] per component (Qdrant uint8)."""
    n = np.linalg.norm(vecs, axis=1, keepdims=True)
    n[n == 0] = 1.0
    unit = vecs / n
    q = np.clip(np.round((unit * 0.5 + 0.5) * 255.0), 0, 255)
    return q.astype(np.uint8)


def _h(n: float) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=20000)
    ap.add_argument("--limit", type=int, default=None, help="smoke cap")
    args = ap.parse_args()

    import chromadb

    s = load_settings()
    client = chromadb.PersistentClient(path=str(s.chroma_persist_dir))
    coll = client.get_collection(name=s.chroma_collection)
    total = coll.count()
    target = min(total, args.limit) if args.limit else total
    print(f"[i] collection={s.chroma_persist_dir} · total={total:,} · "
          f"exporting={target:,}")

    OUT.mkdir(parents=True, exist_ok=True)
    vec_chunks: list[np.ndarray] = []
    rows: list[dict] = []
    done = 0
    dim = 0
    while done < target:
        n = min(args.batch, target - done)
        got = coll.get(limit=n, offset=done,
                        include=["embeddings", "metadatas"])
        embs = got["embeddings"]
        if embs is None or len(embs) == 0:
            break
        arr = np.asarray(embs, dtype=np.float32)
        dim = arr.shape[1]
        vec_chunks.append(_quantize_uint8(arr))
        for m in got["metadatas"] or []:
            rows.append({k: m.get(k) for k in PAYLOAD_KEYS})
        done += len(embs)
        print(f"    {done:,}/{target:,}")

    vecs = np.concatenate(vec_chunks, axis=0)
    df = pd.DataFrame(rows)
    np.save(OUT / "vectors_uint8.npy", vecs)
    df.to_parquet(OUT / "payload.parquet", index=False)

    v_bytes = (OUT / "vectors_uint8.npy").stat().st_size
    p_bytes = (OUT / "payload.parquet").stat().st_size
    # Qdrant on-disk ≈ uint8 vectors + HNSW graph (~M*8 bytes/pt, M=16) +
    # payload + index overhead. Rough ×1.3 of (vec+payload).
    est_qdrant = (v_bytes + p_bytes) * 1.3
    meta = {
        "count": int(vecs.shape[0]),
        "dim": int(dim),
        "scheme": "L2norm->uint8[-1,1]->[0,255]; Qdrant datatype=uint8, cosine",
        "vectors_uint8_bytes": int(v_bytes),
        "payload_parquet_bytes": int(p_bytes),
        "est_qdrant_on_disk": int(est_qdrant),
        "abstracts": "NOT included — served by tez_no from "
                     "data/derived/abstracts_filtered_clean.parquet (D5b.2)",
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("\n[+] Export done:")
    print(f"    vectors_uint8.npy : {_h(v_bytes)}  ({vecs.shape})")
    print(f"    payload.parquet   : {_h(p_bytes)}")
    print(f"    est. Qdrant on-disk: ~{_h(est_qdrant)}  "
          f"({'FITS ~1GB free tier' if est_qdrant < 1024**3 else 'OVER 1GB'})")
    print(f"    → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
