"""Stage 2 (Yol 2) — cross-encoder reranker over retrieved theses.

Why: the Stage 2b diagnostic empirically showed the RAG bottleneck is
retrieval *grounding*, not the writer LM (teacher faithfulness ~0.5,
holistic ~2.3, uniform across domains; rejection-sample keep-rate ~13% at
calibrated thresholds). A bi-encoder (trakad-embed-v2) returns topically
close but often weakly-supporting abstracts → the writer faithfully
reproduces weak context. A cross-encoder re-scores each (question, abstract)
pair jointly and filters this noise — the direct lever for the documented
Corpus Expansion Paradox.

Design (mirrors the LIVE_SEARCH env-toggle pattern so baseline vs rerank is
a clean A/B, like the v1/v2 eval split):

    TRRESEARCHER_RERANK=1            enable (default OFF → behaviour unchanged)
    RERANK_MODEL=BAAI/bge-reranker-base
    RERANK_TOP_N=10                 keep this many after reranking
    RERANK_DEVICE=cpu               'cuda' is much faster if torch sees the GPU

Reranks on title + full abstract (RetrievedChunk.abstract_tr), not the
truncated excerpt. Model is lazy-loaded and cached.
"""
from __future__ import annotations

import os
from functools import lru_cache

from ..schemas import RetrievedChunk

# Product default = ON (measured: +0.09 citation accuracy, 30-q A/B).
# Set TRRESEARCHER_RERANK=0 to reproduce the v2 no-rerank baseline.
RERANK_ENABLED = os.getenv("TRRESEARCHER_RERANK", "1") == "1"


def _cfg() -> tuple[str, int, str]:
    return (
        os.getenv("RERANK_MODEL", "BAAI/bge-reranker-base"),
        int(os.getenv("RERANK_TOP_N", "10")),
        os.getenv("RERANK_DEVICE", "cpu"),
    )


@lru_cache(maxsize=1)
def _model(model_name: str, device: str):
    # CrossEncoder wraps AutoModelForSequenceClassification (num_labels=1),
    # which is what bge-reranker-* expose. Already available via the
    # sentence-transformers dep used for the embedder — no new requirement.
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name, max_length=512, device=device)


def _passage(c: RetrievedChunk) -> str:
    """What the cross-encoder scores against the query. Title gives topical
    anchor; abstract gives the actual supporting evidence."""
    title = (c.title_tr or "").strip()
    body = (c.abstract_tr or "").strip()
    return f"{title}\n{body}" if title else body


def rerank(query: str, chunks: list[RetrievedChunk],
           top_n: int | None = None) -> list[RetrievedChunk]:
    """Re-score `chunks` against `query` with a cross-encoder, return the
    top_n re-ordered. The cross-encoder score is written back into
    `chunk.score` so downstream code (synthesizer/writer/eval) keeps using
    the same field; original bi-encoder order is replaced.

    Falls back to the input (truncated to top_n) on any failure — reranking
    must never harden into a new single point of failure for the pipeline.
    """
    if not chunks:
        return chunks
    model_name, env_top_n, device = _cfg()
    n = top_n if top_n is not None else env_top_n
    try:
        model = _model(model_name, device)
        pairs = [(query, _passage(c)) for c in chunks]
        scores = model.predict(pairs, batch_size=16, show_progress_bar=False)
        ranked = sorted(zip(chunks, scores), key=lambda t: float(t[1]), reverse=True)
        out: list[RetrievedChunk] = []
        for c, s in ranked[:n]:
            c.score = float(s)
            out.append(c)
        return out
    except Exception as e:  # pragma: no cover - defensive
        import sys
        print(f"[reranker] disabled this call ({e}); using bi-encoder order",
              file=sys.stderr)
        return chunks[:n]
