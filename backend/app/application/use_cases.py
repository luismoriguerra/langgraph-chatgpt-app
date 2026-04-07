import uuid
from collections.abc import AsyncIterator
from datetime import datetime

import structlog

from app.domain.entities import Conversation, Message
from app.domain.ports import ConversationRepository, LLMService, MessageRepository

logger = structlog.get_logger()


async def create_conversation(
    repo: ConversationRepository,
    title: str = "New conversation...",
) -> Conversation:
    now = datetime.utcnow()
    conversation = Conversation(id=uuid.uuid4(), title=title, created_at=now, updated_at=now)
    return await repo.create(conversation)


async def send_message(
    conversation_id: uuid.UUID,
    user_content: str,
    conv_repo: ConversationRepository,
    msg_repo: MessageRepository,
    llm_service: LLMService,
) -> AsyncIterator[str]:
    conversation = await conv_repo.get_by_id(conversation_id)
    if not conversation:
        raise ValueError(f"Conversation {conversation_id} not found")

    user_message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role="user",
        content=user_content,
        created_at=datetime.utcnow(),
    )
    await msg_repo.create(user_message)

    history = await msg_repo.list_by_conversation(conversation_id)

    logger.info(
        "use_case.send_message",
        conversation_id=str(conversation_id),
        history_length=len(history),
    )

    full_response: list[str] = []

    async for token in llm_service.stream_chat(history):
        full_response.append(token)
        yield token

    assistant_message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role="assistant",
        content="".join(full_response),
        created_at=datetime.utcnow(),
    )
    await msg_repo.create(assistant_message)
    await conv_repo.update_timestamp(conversation_id)

    is_first_message = len(history) == 1
    if is_first_message:
        yield ""  # signal that stream is done before background title gen
        try:
            title = await llm_service.generate_title(user_content)
            await conv_repo.update_title(conversation_id, title)
            logger.info("use_case.title_generated", title=title)
        except Exception:
            fallback = user_content[:50] + ("..." if len(user_content) > 50 else "")
            await conv_repo.update_title(conversation_id, fallback)
            logger.warning("use_case.title_fallback", fallback=fallback)
