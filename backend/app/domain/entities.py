from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Conversation:
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Message:
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
    tool_invocations: list[ToolInvocation] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {self.role!r}. Must be 'user' or 'assistant'.")
        if not self.content or not self.content.strip():
            raise ValueError("Message content must not be empty or whitespace-only.")


@dataclass(frozen=True)
class SearchResult:
    title: str
    snippet: str
    url: str


@dataclass(frozen=True)
class ToolInvocation:
    id: UUID
    message_id: UUID
    tool_name: str
    tool_input: str
    tool_output: list[SearchResult]
    created_at: datetime
    tool_result: str = ""
