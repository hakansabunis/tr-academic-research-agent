"""Qdrant backend (D2.1) — hosted free-tier vector store.

Stores vectors as Qdrant `datatype: uint8` (no float32 originals → fits the
~1 GB free tier). Query embeddings are quantized the SAME way as the export
(scripts/31_export_qdrant.py) so search is consistent. Payload holds only
minimal citation metadata; the full abstract is rehydrated by tez_no via
tools.abstract_store (→ no quality compromise).

Activated by env (chroma stays the default — local setup unchanged):
    VECTOR_BACKEND=qdrant
    QDRANT_URL=https://xxxx.cloud.qdrant.io:6333
    QDRANT_API_KEY=...                 (put in .env, never in chat)
    QDRANT_COLLECTION=turkish_theses_v2
"""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np

COLLECTION = os.getenv("QDRANT_COLLECTION", "turkish_theses_v2")
PAYLOAD_KEYS = ("tez_no", "title_tr", "author", "year", "advisor",
                "location", "pdf_url")


def quantize_uint8(vecs: np.ndarray) -> np.ndarray:
    """MUST match scripts/31_export_qdrant.py exactly."""
    vecs = np.asarray(vecs, dtype=np.float32)
    if vecs.ndim == 1:
        vecs = vecs[None, :]
    n = np.linalg.norm(vecs, axis=1, keepdims=True)
    n[n == 0] = 1.0
    unit = vecs / n
    return np.clip(np.round((unit * 0.5 + 0.5) * 255.0), 0, 255).astype(np.uint8)


@lru_cache(maxsize=1)
def _client():
    from qdrant_client import QdrantClient

    url = os.getenv("QDRANT_URL")
    if not url:
        raise RuntimeError("QDRANT_URL not set (see .env / D2 docs).")
    return QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY"),
                        timeout=30)


def search(query_vec: np.ndarray, k: int = 6) -> list[dict]:
    """Return [{score, **payload}] for one query embedding (float32 in)."""
    qv = quantize_uint8(query_vec)[0].tolist()
    res = _client().search(
        collection_name=COLLECTION,
        query_vector=qv,
        limit=k,
        with_payload=True,
    )
    out = []
    for p in res:
        rec = {k_: (p.payload or {}).get(k_) for k_ in PAYLOAD_KEYS}
        rec["score"] = float(p.score)
        out.append(rec)
    return out
