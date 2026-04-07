import uuid
from datetime import UTC, datetime

import pytest

from app.domain.entities import Conversation, Message


class TestConversation:
    def test_create_conversation(self) -> None:
        now = datetime.now(UTC)
        conv = Conversation(id=uuid.uuid4(), title="Hello", created_at=now, updated_at=now)
        assert conv.title == "Hello"
        assert conv.created_at == now

    def test_conversation_is_frozen(self) -> None:
        now = datetime.now(UTC)
        conv = Conversation(id=uuid.uuid4(), title="Hello", created_at=now, updated_at=now)
        with pytest.raises(AttributeError):
            conv.title = "Changed"  # type: ignore[misc]


class TestMessage:
    def test_create_user_message(self) -> None:
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            role="user",
            content="Hi there",
            created_at=datetime.now(UTC),
        )
        assert msg.role == "user"
        assert msg.content == "Hi there"

    def test_create_assistant_message(self) -> None:
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            role="assistant",
            content="Hello! How can I help?",
            created_at=datetime.now(UTC),
        )
        assert msg.role == "assistant"

    def test_invalid_role_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid role"):
            Message(
                id=uuid.uuid4(),
                conversation_id=uuid.uuid4(),
                role="system",
                content="Not allowed",
                created_at=datetime.now(UTC),
            )

    def test_empty_content_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            Message(
                id=uuid.uuid4(),
                conversation_id=uuid.uuid4(),
                role="user",
                content="",
                created_at=datetime.now(UTC),
            )

    def test_whitespace_only_content_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            Message(
                id=uuid.uuid4(),
                conversation_id=uuid.uuid4(),
                role="user",
                content="   \n\t  ",
                created_at=datetime.now(UTC),
            )

    def test_message_is_frozen(self) -> None:
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            role="user",
            content="Hello",
            created_at=datetime.now(UTC),
        )
        with pytest.raises(AttributeError):
            msg.content = "Changed"  # type: ignore[misc]
