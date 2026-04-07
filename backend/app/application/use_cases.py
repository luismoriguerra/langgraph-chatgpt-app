import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import structlog

from app.domain.entities import Conversation, Message, SearchResult, ToolInvocation
from app.domain.ports import (
    ChatEvent,
    ConversationRepository,
    LLMService,
    MessageRepository,
    ToolInvocationRepository,
)

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


async def send_message_with_agent(
    conversation_id: uuid.UUID,
    user_content: str,
    conv_repo: ConversationRepository,
    msg_repo: MessageRepository,
    tool_repo: ToolInvocationRepository,
    llm_service: LLMService,
) -> AsyncIterator[ChatEvent]:
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
        "use_case.send_message_with_agent",
        conversation_id=str(conversation_id),
        history_length=len(history),
    )

    full_response: list[str] = []
    collected_tools: list[dict[str, Any]] = []

    async for event in llm_service.stream_agent_chat(history):
        yield event

        if event["type"] == "text-delta":
            full_response.append(event["data"]["textDelta"])
        elif event["type"] == "tool-start":
            collected_tools.append({
                "tool_name": event["data"]["toolName"],
                "tool_input": json.dumps(event["data"]["toolInput"])
                if not isinstance(event["data"]["toolInput"], str)
                else event["data"]["toolInput"],
                "sources": [],
            })
        elif event["type"] == "sources" and collected_tools:
            collected_tools[-1]["sources"] = event["data"]["sources"]

    assistant_content = "".join(full_response)
    if not assistant_content.strip():
        assistant_content = "I couldn't generate a response."

    assistant_message = Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
        created_at=datetime.utcnow(),
    )
    await msg_repo.create(assistant_message)

    for tool_data in collected_tools:
        invocation = ToolInvocation(
            id=uuid.uuid4(),
            message_id=assistant_message.id,
            tool_name=tool_data["tool_name"],
            tool_input=tool_data["tool_input"],
            tool_output=[
                SearchResult(
                    title=s.get("title", ""),
                    snippet=s.get("snippet", ""),
                    url=s.get("url", ""),
                )
                for s in tool_data["sources"]
            ],
            created_at=datetime.utcnow(),
        )
        await tool_repo.create(invocation)

    await conv_repo.update_timestamp(conversation_id)

    is_first_message = len(history) == 1
    if is_first_message:
        try:
            title = await llm_service.generate_title(user_content)
            await conv_repo.update_title(conversation_id, title)
            logger.info("use_case.agent_title_generated", title=title)
        except Exception:
            fallback = user_content[:50] + ("..." if len(user_content) > 50 else "")
            await conv_repo.update_title(conversation_id, fallback)
            logger.warning("use_case.agent_title_fallback", fallback=fallback)
