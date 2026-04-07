import uuid
from datetime import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.entities import Conversation
from app.infrastructure.repositories import (
    SqlAlchemyConversationRepository,
    SqlAlchemyMessageRepository,
)
from app.presentation.dependencies import get_conversation_repo, get_message_repo
from app.presentation.schemas import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    UpdateConversationRequest,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    repo: Annotated[SqlAlchemyConversationRepository, Depends(get_conversation_repo)] = ...,  # type: ignore[assignment]
) -> ConversationListResponse:
    conversations = await repo.list_recent(limit=limit, offset=offset)
    total = await repo.count()
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c.__dict__) for c in conversations],
        total=total,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    conv_repo: Annotated[SqlAlchemyConversationRepository, Depends(get_conversation_repo)] = ...,  # type: ignore[assignment]
    msg_repo: Annotated[SqlAlchemyMessageRepository, Depends(get_message_repo)] = ...,  # type: ignore[assignment]
) -> ConversationDetailResponse:
    conversation = await conv_repo.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await msg_repo.list_by_conversation(conversation_id)
    return ConversationDetailResponse(
        **ConversationResponse.model_validate(conversation.__dict__).model_dump(),
        messages=[MessageResponse.model_validate(m.__dict__) for m in messages],
    )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: CreateConversationRequest,
    repo: Annotated[SqlAlchemyConversationRepository, Depends(get_conversation_repo)] = ...,  # type: ignore[assignment]
) -> ConversationResponse:
    now = datetime.utcnow()
    conversation = Conversation(
        id=uuid.uuid4(),
        title=body.title,
        created_at=now,
        updated_at=now,
    )
    created = await repo.create(conversation)
    return ConversationResponse.model_validate(created.__dict__)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: uuid.UUID,
    body: UpdateConversationRequest,
    repo: Annotated[SqlAlchemyConversationRepository, Depends(get_conversation_repo)] = ...,  # type: ignore[assignment]
) -> ConversationResponse:
    conversation = await repo.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await repo.update_title(conversation_id, body.title)
    updated = await repo.get_by_id(conversation_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(updated.__dict__)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    repo: Annotated[SqlAlchemyConversationRepository, Depends(get_conversation_repo)] = ...,  # type: ignore[assignment]
) -> None:
    conversation = await repo.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await repo.delete(conversation_id)
