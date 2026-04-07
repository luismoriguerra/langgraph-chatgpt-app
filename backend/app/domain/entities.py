from __future__ import annotations

from dataclasses import dataclass
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

    def __post_init__(self) -> None:
        if self.role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {self.role!r}. Must be 'user' or 'assistant'.")
        if not self.content or not self.content.strip():
            raise ValueError("Message content must not be empty or whitespace-only.")
