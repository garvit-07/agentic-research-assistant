"""Helpers that run the graph: one-shot (JSON) and streaming (SSE events)."""
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.agent.state import new_turn_input
from app.config import settings
from app.utils import text_of, truncate

logger = logging.getLogger(__name__)

NODES = {"planner", "researcher", "writer", "reviewer", "finalize"}


def _config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": settings.recursion_limit}


def _result_payload(thread_id: str, values: dict[str, Any]) -> dict[str, Any]:
    return {
        "thread_id": thread_id,
        "answer": values.get("final_answer", ""),
        "plan": values.get("plan", []),
        "sources": values.get("sources", []),
        "review": values.get("review"),
        "drafts": values.get("revision_count", 1),
    }


async def run_once(graph, message: str, thread_id: str) -> dict[str, Any]:
    values = await graph.ainvoke(new_turn_input(message), _config(thread_id))
    return _result_payload(thread_id, values)


async def stream_events(graph, message: str, thread_id: str) -> AsyncIterator[dict[str, Any]]:
    """Yield {'event': str, 'data': dict} items describing the agent's progress in real time.

    Events: start, node_start, plan, tool_start, tool_end, token, review, final, done.
    """
    cfg = _config(thread_id)
    yield {"event": "start", "data": {"thread_id": thread_id}}

    async for ev in graph.astream_events(new_turn_input(message), cfg, version="v2"):
        kind, name = ev["event"], ev.get("name")
        node = (ev.get("metadata") or {}).get("langgraph_node")

        if kind == "on_chain_start" and name in NODES and node == name:
            yield {"event": "node_start", "data": {"node": name}}

        elif kind == "on_chat_model_stream" and node == "writer":
            text = text_of(ev["data"]["chunk"].content)
            if text:
                yield {"event": "token", "data": {"text": text}}

        elif kind == "on_tool_start":
            yield {"event": "tool_start", "data": {"tool": name, "input": ev["data"].get("input")}}

        elif kind == "on_tool_end":
            out = ev["data"].get("output")
            out = getattr(out, "content", out)
            yield {"event": "tool_end", "data": {"tool": name, "preview": truncate(str(out), 400)}}

        elif kind == "on_chain_end" and name in NODES and node == name:
            output = ev["data"].get("output") or {}
            if name == "planner":
                yield {"event": "plan", "data": {"steps": output.get("plan", [])}}
            elif name == "reviewer":
                yield {"event": "review", "data": output.get("review")}

    snapshot = await graph.aget_state(cfg)
    yield {"event": "final", "data": _result_payload(thread_id, snapshot.values)}
    yield {"event": "done", "data": {}}
