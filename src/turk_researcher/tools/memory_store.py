"""In-process vector search (D2 — HF-only, no external DB).

The free HF Space (16 GB RAM) loads the uint8 export once and does
brute-force cosine in numpy. 633K×768 is a single matmul (~hundreds of ms
on CPU) — negligible vs the 2–4 min LLM stage, so no HNSW/DB is needed.
This removes the Qdrant account entirely; everything is HF-hosted.

Quality: uint8 is dequantized back to ~unit vectors (inverse of
scripts/31_export_qdrant.py) so cosine is near full-precision; the
cross-encoder reranker recovers the rest → no quality compromise.

Artifacts (env-overridable; on a Space, pulled from the HF index dataset):
    MEMSTORE_DIR   default: data/derived/qdrant_export
        vectors_uint8.npy  (N,768) uint8
        payload.parquet    tez_no,title_tr,author,year,advisor,location,pdf_url
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PAYLOAD_KEYS = ("tez_no", "title_tr", "author", "year", "advisor",
                "location", "pdf_url")


def _dir() -> Path:
    return Path(os.getenv("MEMSTORE_DIR",
                          str(ROOT / "data" / "derived" / "qdrant_export")))


@lru_cache(maxsize=1)
def _index():
    import pandas as pd

    d = _dir()
    vp, pp = d / "vectors_uint8.npy", d / "payload.parquet"
    if not vp.exists() or not pp.exists():
        raise RuntimeError(
            f"Memory store artifacts missing in {d} — run "
            f"scripts/31_export_qdrant.py (or pull from the HF dataset).")
    u8 = np.load(vp)                       # (N,768) uint8
    # inverse of export: uint8 → [-1,1] → L2-normalize
    f = (u8.astype(np.float32) / 255.0 - 0.5) * 2.0
    f /= np.clip(np.linalg.norm(f, axis=1, keepdims=True), 1e-9, None)
    pay = pd.read_parquet(pp)
    return f, pay  # f: float32 normalized (~1.9 GB RAM, fits 16 GB Space)


def warm() -> int:
    f, _ = _index()
    return int(f.shape[0])


def search(query_vec: np.ndarray, k: int = 6) -> list[dict]:
    """Top-k by cosine for one query embedding (float32 in)."""
    f, pay = _index()
    q = np.asarray(query_vec, dtype=np.float32).reshape(-1)
    q /= max(float(np.linalg.norm(q)), 1e-9)
    sims = f @ q                                   # (N,)
    k = min(k, sims.shape[0])
    idx = np.argpartition(-sims, k - 1)[:k]
    idx = idx[np.argsort(-sims[idx])]
    out = []
    for i in idx:
        row = pay.iloc[int(i)]
        rec = {kk: (None if (kk in pay.columns and _isna(row[kk])) else
                    (row[kk] if kk in pay.columns else None))
               for kk in PAYLOAD_KEYS}
        rec["score"] = float(sims[int(i)])
        out.append(rec)
    return out


def _isna(v) -> bool:
    try:
        import pandas as pd
        return bool(pd.isna(v))
    except Exception:
        return v is None
