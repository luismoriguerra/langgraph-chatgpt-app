import json
import uuid
from collections.abc import AsyncIterator, Callable
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application import use_cases
from app.infrastructure.database import get_db_session
from app.infrastructure.llm_service import OpenAILLMService
from app.infrastructure.repositories import (
    SqlAlchemyConversationRepository,
    SqlAlchemyMessageRepository,
    SqlAlchemyToolInvocationRepository,
)
from app.presentation.schemas import SendMessageRequest

logger = structlog.get_logger()

router = APIRouter(prefix="/api/conversations", tags=["chat"])

_SSE_SERIALIZERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "text-delta": lambda d: {"type": "text-delta", "textDelta": d["textDelta"]},
    "tool-start": lambda d: {
        "type": "tool-start",
        "toolName": d["toolName"],
        "toolInput": d["toolInput"],
    },
    "tool-end": lambda d: {"type": "tool-end", "toolName": d["toolName"]},
    "sources": lambda d: {"type": "sources", "sources": d["sources"]},
    "tool-result": lambda d: {
        "type": "tool-result",
        "toolName": d["toolName"],
        "toolInput": d["toolInput"],
        "result": d["result"],
    },
}


@router.post("/{conversation_id}/chat")
async def chat_stream(
    conversation_id: uuid.UUID,
    body: SendMessageRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StreamingResponse:
    conv_repo = SqlAlchemyConversationRepository(session)
    msg_repo = SqlAlchemyMessageRepository(session)
    tool_repo = SqlAlchemyToolInvocationRepository(session)
    llm_service = OpenAILLMService()

    conversation = await conv_repo.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for event in use_cases.send_message_with_agent(
                conversation_id=conversation_id,
                user_content=body.message,
                conv_repo=conv_repo,
                msg_repo=msg_repo,
                tool_repo=tool_repo,
                llm_service=llm_service,
            ):
                serializer = _SSE_SERIALIZERS.get(event["type"])
                if serializer:
                    yield f"data: {json.dumps(serializer(event['data']))}\n\n"

            finish = json.dumps({"type": "finish", "finishReason": "stop"})
            yield f"data: {finish}\n\n"

        except Exception as e:
            logger.error("chat.stream.error", error=str(e))
            error_data = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
