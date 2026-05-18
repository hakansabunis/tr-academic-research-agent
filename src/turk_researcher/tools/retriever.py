from __future__ import annotations

import os
from typing import Iterable

from ..schemas import RetrievedChunk
from ..vectorstore import get_collection, get_encoder


def _doc_to_chunk(doc: str, metadata: dict, distance: float) -> RetrievedChunk:
    md = metadata or {}
    title = md.get("title_tr") or ""
    abstract = doc or ""
    # Document was indexed as title + "\n\n" + abstract; strip the title prefix
    # for a clean abstract.
    if title and abstract.startswith(title):
        abstract = abstract[len(title):].lstrip("\n")

    year_raw = md.get("year")
    try:
        year = int(year_raw) if year_raw not in (None, "", 0) else None
    except (TypeError, ValueError):
        year = None

    # Cosine distance is in [0, 2]; convert to similarity in [0, 1] for the
    # rest of the pipeline. (1 - distance/2 gives us a monotonic score.)
    score = max(0.0, 1.0 - float(distance) / 2.0)

    return RetrievedChunk(
        tez_no=str(md.get("tez_no", "")),
        title_tr=title,
        author=str(md.get("author", "")),
        advisor=md.get("advisor") or None,
        location=md.get("location") or None,
        year=year,
        abstract_tr=abstract.strip(),
        score=score,
        pdf_url=md.get("pdf_url") or None,
    )


def _retrieve_external(queries: Iterable[str], k: int, encoder, search_fn) -> list[RetrievedChunk]:
    """Hosted path: external / in-memory store returns minimal payload;
    full abstract rehydrated by tez_no (no quality compromise)."""
    from .abstract_store import get_abstract

    seen: dict[str, RetrievedChunk] = {}
    for q in queries:
        if not q or not q.strip():
            continue
        qv = encoder.encode(q.strip(), normalize_embeddings=True)
        for r in search_fn(qv, k=k):
            tez = str(r.get("tez_no") or "")
            if not tez:
                continue
            yr = r.get("year")
            try:
                yr = int(yr) if yr not in (None, "", 0) else None
            except (TypeError, ValueError):
                yr = None
            score = float(r.get("score") or 0.0)
            ex = seen.get(tez)
            if ex is not None and ex.score >= score:
                continue
            seen[tez] = RetrievedChunk(
                tez_no=tez,
                title_tr=r.get("title_tr") or "",
                author=str(r.get("author") or ""),
                advisor=r.get("advisor") or None,
                location=r.get("location") or None,
                year=yr,
                abstract_tr=get_abstract(tez),
                score=score,
                pdf_url=r.get("pdf_url") or None,
            )
    return sorted(seen.values(), key=lambda c: c.score, reverse=True)


def retrieve(queries: Iterable[str], *, k: int = 6) -> list[RetrievedChunk]:
    """Multi-query retrieval — embeds each query, dedupes by tez_no, keeps
    best score. Backend via VECTOR_BACKEND env: 'chroma' (default → local
    setup unchanged) or 'qdrant' (hosted free tier + abstract rehydration)."""
    encoder = get_encoder()
    backend = os.getenv("VECTOR_BACKEND", "chroma").lower()
    if backend == "qdrant":
        from .qdrant_store import search as _s
        return _retrieve_external(queries, k, encoder, _s)
    if backend == "memory":
        from .memory_store import search as _s
        return _retrieve_external(queries, k, encoder, _s)

    coll = get_collection()
    seen: dict[str, RetrievedChunk] = {}

    for q in queries:
        if not q or not q.strip():
            continue
        qv = encoder.encode(q.strip(), normalize_embeddings=True).tolist()
        res = coll.query(
            query_embeddings=[qv],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            chunk = _doc_to_chunk(doc, meta or {}, dist)
            if not chunk.tez_no:
                continue
            existing = seen.get(chunk.tez_no)
            if existing is None or chunk.score > existing.score:
                seen[chunk.tez_no] = chunk

    return sorted(seen.values(), key=lambda c: c.score, reverse=True)
