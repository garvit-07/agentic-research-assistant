from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph import (
    build_graph,
    route_after_planner,
    route_after_researcher,
    route_after_review,
)
from app.config import settings


def test_graph_has_expected_nodes():
    graph = build_graph(MemorySaver())
    nodes = set(graph.get_graph().nodes)
    assert {"planner", "researcher", "writer", "reviewer", "finalize"} <= nodes


def test_planner_routing():
    assert route_after_planner({"plan": ["a"]}) == "researcher"
    assert route_after_planner({"plan": []}) == "writer"


def test_researcher_loops_until_plan_done():
    state = {"plan": ["a", "b"], "current_step": 1}
    assert route_after_researcher(state) == "researcher"
    assert route_after_researcher({"plan": ["a", "b"], "current_step": 2}) == "writer"


def test_review_routing_approve_revise_and_budget():
    assert route_after_review({"review": {"approved": True}, "revision_count": 1}) == "finalize"
    assert route_after_review({"review": {"approved": False}, "revision_count": 1}) == "writer"
    exhausted = settings.max_revisions + 1
    assert route_after_review({"review": {"approved": False}, "revision_count": exhausted}) == "finalize"
