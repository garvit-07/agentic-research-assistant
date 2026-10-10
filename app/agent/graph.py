"""Graph wiring.

START -> planner -> (researcher loop | writer) -> writer -> reviewer -> (writer | finalize) -> END
"""
from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import finalize, planner, researcher, reviewer, writer
from app.agent.state import AgentState
from app.config import settings


def route_after_planner(state: AgentState) -> Literal["researcher", "writer"]:
    return "researcher" if state.get("plan") else "writer"


def route_after_researcher(state: AgentState) -> Literal["researcher", "writer"]:
    return "researcher" if state.get("current_step", 0) < len(state.get("plan", [])) else "writer"


def route_after_review(state: AgentState) -> Literal["writer", "finalize"]:
    approved = (state.get("review") or {}).get("approved", False)
    out_of_budget = state.get("revision_count", 0) >= settings.max_revisions + 1
    return "finalize" if approved or out_of_budget else "writer"


def build_graph(checkpointer=None):
    g = StateGraph(AgentState)
    g.add_node("planner", planner)
    g.add_node("researcher", researcher)
    g.add_node("writer", writer)
    g.add_node("reviewer", reviewer)
    g.add_node("finalize", finalize)

    g.add_edge(START, "planner")
    g.add_conditional_edges(
        "planner", route_after_planner, {"researcher": "researcher", "writer": "writer"}
    )
    g.add_conditional_edges(
        "researcher", route_after_researcher, {"researcher": "researcher", "writer": "writer"}
    )
    g.add_edge("writer", "reviewer")
    g.add_conditional_edges(
        "reviewer", route_after_review, {"writer": "writer", "finalize": "finalize"}
    )
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)
