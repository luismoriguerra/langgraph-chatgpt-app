import json
import uuid
from typing import Annotated

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
)
from app.presentation.schemas import SendMessageRequest

logger = structlog.get_logger()

router = APIRouter(prefix="/api/conversations", tags=["chat"])


@router.post("/{conversation_id}/chat")
async def chat_stream(
    conversation_id: uuid.UUID,
    body: SendMessageRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StreamingResponse:
    conv_repo = SqlAlchemyConversationRepository(session)
    msg_repo = SqlAlchemyMessageRepository(session)
    llm_service = OpenAILLMService()

    conversation = await conv_repo.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    async def event_stream():  # type: ignore[no-untyped-def]
        try:
            async for token in use_cases.send_message(
                conversation_id=conversation_id,
                user_content=body.message,
                conv_repo=conv_repo,
                msg_repo=msg_repo,
                llm_service=llm_service,
            ):
                if token:
                    data = json.dumps({"type": "text-delta", "textDelta": token})
                    yield f"data: {data}\n\n"

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
