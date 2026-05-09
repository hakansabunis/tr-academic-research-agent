from __future__ import annotations

import os

from langgraph.graph import END, StateGraph

from .agents.critic import critic_node
from .agents.live_search_node import live_search_node
from .agents.planner import planner_node
from .agents.retriever_node import retriever_node
from .agents.synthesizer import synthesizer_node
from .agents.writer import writer_node
from .schemas import GraphState

MAX_CRITIC_LOOPS = 2

# Toggle live API augmentation. Set TRRESEARCHER_LIVE=0 to disable.
LIVE_SEARCH_ENABLED = os.getenv("TRRESEARCHER_LIVE", "1") == "1"


def _critic_router(state: GraphState) -> str:
    """Route after Critic:
    - If coverage_ok or requery_terms empty: go to Writer.
    - Else if iteration >= MAX_CRITIC_LOOPS: go to Writer.
    - Else first failure: try local Retriever again.
    - On second failure (iteration == MAX_CRITIC_LOOPS - 1) and live search is
      enabled: hop to live_search before writing.
    """
    critic = state.get("critic")
    iteration = state.get("iteration", 0)
    if critic is None or critic.coverage_ok or not critic.requery_terms:
        return "writer"
    if iteration >= MAX_CRITIC_LOOPS:
        return "live_search" if LIVE_SEARCH_ENABLED else "writer"
    return "retriever"


def build_graph():
    g = StateGraph(GraphState)
    g.add_node("planner", planner_node)
    g.add_node("retriever", retriever_node)
    g.add_node("synthesizer", synthesizer_node)
    g.add_node("critic", critic_node)
    g.add_node("live_search", live_search_node)
    g.add_node("writer", writer_node)

    g.set_entry_point("planner")
    g.add_edge("planner", "retriever")
    g.add_edge("retriever", "synthesizer")
    g.add_edge("synthesizer", "critic")
    g.add_conditional_edges(
        "critic",
        _critic_router,
        {"retriever": "retriever", "live_search": "live_search", "writer": "writer"},
    )
    g.add_edge("live_search", "writer")
    g.add_edge("writer", END)

    return g.compile()
