from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    thread_id: str | None = Field(
        default=None, description="Conversation id. Reuse it to continue with memory."
    )


class ReviewOut(BaseModel):
    approved: bool
    score: int
    issues: list[str]
    feedback: str


class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    plan: list[str]
    sources: list[str]
    review: ReviewOut | None = None
    drafts: int = 1


class HistoryMessage(BaseModel):
    role: str
    content: str


class ThreadHistory(BaseModel):
    thread_id: str
    messages: list[HistoryMessage]


class UploadResponse(BaseModel):
    filename: str
    chunks: int
