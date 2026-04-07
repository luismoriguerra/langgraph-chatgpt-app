import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.domain.entities import Conversation, Message


@pytest.fixture
def make_conversation():
    def _make(
        title: str = "Test conversation",
        id: uuid.UUID | None = None,
    ) -> Conversation:
        now = datetime.now(timezone.utc)
        return Conversation(
            id=id or uuid.uuid4(),
            title=title,
            created_at=now,
            updated_at=now,
        )
    return _make


@pytest.fixture
def make_message():
    def _make(
        conversation_id: uuid.UUID | None = None,
        role: str = "user",
        content: str = "Hello",
        id: uuid.UUID | None = None,
    ) -> Message:
        return Message(
            id=id or uuid.uuid4(),
            conversation_id=conversation_id or uuid.uuid4(),
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
    return _make


@pytest.fixture
def mock_conversation_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.list_recent = AsyncMock(return_value=[])
    repo.count = AsyncMock(return_value=0)
    repo.update_title = AsyncMock()
    repo.update_timestamp = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_message_repo():
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.list_by_conversation = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_llm_service():
    service = AsyncMock()

    async def fake_stream(*args, **kwargs):  # type: ignore[no-untyped-def]
        for token in ["Hello", " from", " AI"]:
            yield token

    service.stream_chat = fake_stream
    service.generate_title = AsyncMock(return_value="Test Title")
    return service
