from __future__ import annotations

import os

from ..schemas import GraphState
from ..tools.reranker import RERANK_ENABLED, rerank
from ..tools.retriever import retrieve


def retriever_node(state: GraphState) -> GraphState:
    queries: list[str] = [state["question"]]
    plan = state.get("plan")
    if plan is not None:
        queries.extend(sq.text for sq in plan.sub_questions)

    critic = state.get("critic")
    if critic is not None and critic.requery_terms:
        queries.extend(critic.requery_terms)

    if RERANK_ENABLED:
        # Cast a wider net for the cross-encoder to filter (Yol 2). The
        # original question is the rerank query — the cleanest relevance
        # signal. Default OFF → identical to the v2 baseline below.
        cand_k = int(os.getenv("RERANK_CANDIDATES_K", "12"))
        max_cand = int(os.getenv("RERANK_MAX_CANDIDATES", "60"))
        chunks = retrieve(queries, k=cand_k)[:max_cand]
        chunks = rerank(state["question"], chunks)
    else:
        chunks = retrieve(queries, k=6)
        chunks = chunks[:24]
    return {"chunks": chunks}
