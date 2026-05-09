from __future__ import annotations

from ..schemas import GraphState, RetrievedChunk
from ..tools.live_search import search_live


def live_search_node(state: GraphState) -> GraphState:
    """Run live API tools (OpenAlex, Semantic Scholar, DergiPark) when local
    coverage is insufficient. Uses Critic's `requery_terms` as queries and
    appends the deduplicated results to the existing chunks."""
    critic = state.get("critic")
    queries: list[str] = []
    if critic and critic.requery_terms:
        queries.extend(critic.requery_terms)
    if not queries:
        queries = [state["question"]]

    seen_ids: set[str] = {c.tez_no for c in state.get("chunks", []) if c.tez_no}
    new_chunks: list[RetrievedChunk] = []

    for q in queries[:3]:  # cap to keep latency under control
        per_source = search_live(q, k_each=4)
        for source, chunks in per_source.items():
            for c in chunks:
                key = f"{source}:{c.tez_no}"
                if key in seen_ids or not c.tez_no:
                    continue
                seen_ids.add(key)
                # Tag source in the location/title if missing, so the writer
                # can cite it appropriately.
                if c.location is None or not c.location:
                    c = c.model_copy(update={"location": f"[{source}]"})
                else:
                    c = c.model_copy(update={"location": f"[{source}] {c.location}"})
                new_chunks.append(c)

    if not new_chunks:
        return {}

    return {"chunks": new_chunks}
