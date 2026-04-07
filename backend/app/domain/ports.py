from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from app.domain.entities import Conversation, Message


class ConversationRepository(Protocol):
    async def create(self, conversation: Conversation) -> Conversation: ...

    async def get_by_id(self, id: UUID) -> Conversation | None: ...

    async def list_recent(self, limit: int = 50, offset: int = 0) -> list[Conversation]: ...

    async def count(self) -> int: ...

    async def update_title(self, id: UUID, title: str) -> None: ...

    async def update_timestamp(self, id: UUID) -> None: ...

    async def delete(self, id: UUID) -> None: ...


class MessageRepository(Protocol):
    async def create(self, message: Message) -> Message: ...

    async def list_by_conversation(self, conversation_id: UUID) -> list[Message]: ...


class LLMService(Protocol):
    def stream_chat(
        self, messages: list[Message], system_prompt: str = ""
    ) -> AsyncIterator[str]: ...

    async def generate_title(self, first_message: str) -> str: ...
