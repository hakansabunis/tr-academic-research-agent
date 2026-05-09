from __future__ import annotations

from ..schemas import GraphState
from ..tools.retriever import retrieve


def retriever_node(state: GraphState) -> GraphState:
    queries: list[str] = [state["question"]]
    plan = state.get("plan")
    if plan is not None:
        queries.extend(sq.text for sq in plan.sub_questions)

    critic = state.get("critic")
    if critic is not None and critic.requery_terms:
        queries.extend(critic.requery_terms)

    chunks = retrieve(queries, k=6)
    chunks = chunks[:24]
    return {"chunks": chunks}
