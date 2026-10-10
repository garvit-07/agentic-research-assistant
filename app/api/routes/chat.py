import json
import logging
from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.agent.runner import run_once, stream_events
from app.api.deps import get_graph, verify_api_key
from app.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(verify_api_key)])


def _sse(event: dict) -> str:
    return f"event: {event['event']}\ndata: {json.dumps(event['data'], default=str)}\n\n"


@router.post("", response_model=ChatResponse, summary="Ask a question (single JSON response)")
async def chat(req: ChatRequest, graph=Depends(get_graph)) -> ChatResponse:
    thread_id = req.thread_id or str(uuid4())
    try:
        return ChatResponse(**await run_once(graph, req.message, thread_id))
    except Exception as exc:
        logger.exception("Agent run failed")
        raise HTTPException(502, f"Agent failed: {exc}") from exc


@router.post("/stream", summary="Ask a question (Server-Sent Events stream)")
async def chat_stream(req: ChatRequest, request: Request, graph=Depends(get_graph)):
    thread_id = req.thread_id or str(uuid4())

    async def generator() -> AsyncIterator[str]:
        try:
            async for event in stream_events(graph, req.message, thread_id):
                if await request.is_disconnected():
                    break
                yield _sse(event)
        except Exception as exc:
            logger.exception("Streaming run failed")
            yield _sse({"event": "error", "data": {"message": str(exc)}})

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
