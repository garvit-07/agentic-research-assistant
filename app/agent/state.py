"""Graph state and structured-output schemas."""
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class Plan(BaseModel):
    """Planner output."""

    needs_research: bool = Field(description="True if tools (web / documents) are needed.")
    steps: list[str] = Field(description="Short, independent research sub-tasks. Empty if none needed.")


class Review(BaseModel):
    """Reviewer output (self-critique of the draft)."""

    approved: bool = Field(description="True if the draft is accurate, grounded and complete.")
    score: int = Field(description="Overall quality from 1 (poor) to 10 (excellent).")
    issues: list[str] = Field(description="Concrete problems found. Empty if none.")
    feedback: str = Field(description="Actionable instructions for improving the draft.")


class AgentState(TypedDict, total=False):
    # Conversation memory (persisted by the checkpointer, keyed by thread_id)
    messages: Annotated[list[AnyMessage], add_messages]
    # Per-turn working state (reset at the start of every turn)
    question: str
    plan: list[str]
    current_step: int
    findings: list[dict[str, str]]
    sources: list[str]
    draft: str
    review: dict[str, Any] | None
    revision_count: int
    final_answer: str


def new_turn_input(question: str) -> dict[str, Any]:
    """Initial state for one user turn. Memory (messages) carries over; the rest resets."""
    return {
        "messages": [HumanMessage(content=question)],
        "question": question,
        "plan": [],
        "current_step": 0,
        "findings": [],
        "sources": [],
        "draft": "",
        "review": None,
        "revision_count": 0,
        "final_answer": "",
    }
