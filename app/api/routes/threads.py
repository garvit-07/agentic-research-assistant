from fastapi import APIRouter, Depends, Request

from app.api.deps import get_graph, verify_api_key
from app.schemas import HistoryMessage, ThreadHistory
from app.utils import text_of

router = APIRouter(prefix="/threads", tags=["memory"], dependencies=[Depends(verify_api_key)])


@router.get("/{thread_id}", response_model=ThreadHistory, summary="Conversation history")
async def get_thread(thread_id: str, graph=Depends(get_graph)) -> ThreadHistory:
    snapshot = await graph.aget_state({"configurable": {"thread_id": thread_id}})
    messages = (snapshot.values or {}).get("messages", [])
    return ThreadHistory(
        thread_id=thread_id,
        messages=[
            HistoryMessage(role="user" if m.type == "human" else "assistant", content=text_of(m.content))
            for m in messages
        ],
    )


@router.delete("/{thread_id}", status_code=204, summary="Forget a conversation")
async def delete_thread(thread_id: str, request: Request) -> None:
    await request.app.state.checkpointer.adelete_thread(thread_id)
