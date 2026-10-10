"""LangGraph nodes: planner -> researcher (tool loop) -> writer -> reviewer -> finalize."""
import logging
import re

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig

from app.agent import prompts
from app.agent.llm import get_llm
from app.agent.state import AgentState, Plan, Review
from app.config import settings
from app.tools import TOOLS, TOOLS_BY_NAME
from app.utils import text_of, truncate

logger = logging.getLogger(__name__)

_SOURCE_RE = re.compile(r"^(?:URL|Source): (.+)$", re.MULTILINE)


def _history(messages: list[BaseMessage]) -> str:
    """Render recent prior turns (excluding the current user message) as plain text."""
    prior = messages[:-1][-settings.history_window :]
    lines = [
        f"{'User' if m.type == 'human' else 'Assistant'}: {truncate(text_of(m.content), 800)}"
        for m in prior
    ]
    return "\n".join(lines) or "(no earlier messages)"


def _findings_text(state: AgentState) -> str:
    findings = state.get("findings", [])
    if not findings:
        return "(no research was performed)"
    return "\n\n".join(f"### {f['step']}\n{f['summary']}" for f in findings)


# --------------------------------------------------------------------------- planner
async def planner(state: AgentState, config: RunnableConfig) -> dict:
    llm = get_llm().with_structured_output(Plan)
    plan: Plan = await llm.ainvoke(
        [
            SystemMessage(content=prompts.PLANNER_SYSTEM.format(max_steps=settings.max_plan_steps)),
            HumanMessage(
                content=f"Conversation so far:\n{_history(state['messages'])}\n\n"
                f"New question: {state['question']}"
            ),
        ],
        config=config,
    )
    steps = [s.strip() for s in plan.steps if s.strip()][: settings.max_plan_steps]
    if not plan.needs_research:
        steps = []
    logger.info("Plan: %s", steps)
    return {"plan": steps, "current_step": 0, "findings": [], "sources": []}


# --------------------------------------------------------------------------- researcher
async def researcher(state: AgentState, config: RunnableConfig) -> dict:
    """Executes ONE plan step with a bounded tool-calling loop."""
    idx = state.get("current_step", 0)
    step = state["plan"][idx]
    prior = "\n".join(f"- {f['step']}: {truncate(f['summary'], 300)}" for f in state.get("findings", []))

    msgs: list[BaseMessage] = [
        SystemMessage(content=prompts.RESEARCHER_SYSTEM),
        HumanMessage(
            content=f"Overall question: {state['question']}\n"
            f"Findings so far:\n{prior or '(none)'}\n\nYour research step: {step}"
        ),
    ]
    llm = get_llm()
    llm_tools = llm.bind_tools(TOOLS)
    sources = list(state.get("sources", []))
    ai: AIMessage | None = None

    for _ in range(settings.max_tool_rounds):
        ai = await llm_tools.ainvoke(msgs, config=config)
        msgs.append(ai)
        if not ai.tool_calls:
            break
        for call in ai.tool_calls:
            tool = TOOLS_BY_NAME.get(call["name"])
            try:
                out = await tool.ainvoke(call["args"], config=config) if tool else "Unknown tool."
            except Exception as exc:  # tool failures must not crash the run
                logger.warning("Tool %s failed: %s", call["name"], exc)
                out = f"Tool error: {exc}"
            out = str(out)
            sources.extend(_SOURCE_RE.findall(out))
            msgs.append(ToolMessage(content=out, tool_call_id=call["id"], name=call["name"]))

    if ai is None or ai.tool_calls:  # budget exhausted while still calling tools -> force a summary
        msgs.append(HumanMessage(content="Stop searching and summarise what you found now."))
        ai = await llm.ainvoke(msgs, config=config)

    summary = text_of(ai.content).strip() or "No useful information found."
    return {
        "findings": [*state.get("findings", []), {"step": step, "summary": summary}],
        "sources": list(dict.fromkeys(sources)),  # de-duplicate, keep order
        "current_step": idx + 1,
    }


# --------------------------------------------------------------------------- writer
async def writer(state: AgentState, config: RunnableConfig) -> dict:
    revision_note = ""
    review = state.get("review")
    if review and not review.get("approved"):
        issues = "\n".join(f"- {i}" for i in review.get("issues", []))
        revision_note = (
            "\n\nYour PREVIOUS DRAFT was rejected by the reviewer. Fix the problems.\n"
            f"Issues:\n{issues}\nFeedback: {review.get('feedback', '')}\n"
            f"Previous draft:\n{state.get('draft', '')}"
        )
    resp = await get_llm().ainvoke(
        [
            SystemMessage(content=prompts.WRITER_SYSTEM),
            HumanMessage(
                content=f"Conversation so far:\n{_history(state['messages'])}\n\n"
                f"Question: {state['question']}\n\nResearch findings:\n{_findings_text(state)}"
                f"{revision_note}"
            ),
        ],
        config=config,
    )
    return {"draft": text_of(resp.content), "revision_count": state.get("revision_count", 0) + 1}


# --------------------------------------------------------------------------- reviewer
async def reviewer(state: AgentState, config: RunnableConfig) -> dict:
    llm = get_llm().with_structured_output(Review)
    r: Review = await llm.ainvoke(
        [
            SystemMessage(content=prompts.REVIEWER_SYSTEM),
            HumanMessage(
                content=f"QUESTION:\n{state['question']}\n\nFINDINGS:\n{_findings_text(state)}"
                f"\n\nDRAFT:\n{state['draft']}"
            ),
        ],
        config=config,
    )
    score = max(1, min(10, int(r.score)))
    approved = bool(r.approved) and score >= settings.min_review_score
    logger.info("Review: approved=%s score=%s", approved, score)
    return {"review": {"approved": approved, "score": score, "issues": r.issues, "feedback": r.feedback}}


# --------------------------------------------------------------------------- finalize
async def finalize(state: AgentState) -> dict:
    """Commit the approved (or best-effort) draft to the persisted conversation memory."""
    answer = state["draft"]
    return {"final_answer": answer, "messages": [AIMessage(content=answer)]}
