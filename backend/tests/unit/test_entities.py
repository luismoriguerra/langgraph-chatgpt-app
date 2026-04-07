import uuid
from datetime import UTC, datetime

import pytest

from app.domain.entities import Conversation, Message, SearchResult, ToolInvocation


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


def test_search_result_creation() -> None:
    sr = SearchResult(title="T", snippet="S", url="https://example.com")
    assert sr.title == "T"
    assert sr.snippet == "S"
    assert sr.url == "https://example.com"


def test_tool_invocation_creation() -> None:
    mid = uuid.uuid4()
    results = [
        SearchResult(title="A", snippet="a", url="https://a.test"),
        SearchResult(title="B", snippet="b", url="https://b.test"),
    ]
    inv = ToolInvocation(
        id=uuid.uuid4(),
        message_id=mid,
        tool_name="web_search",
        tool_input='{"q": "hello"}',
        tool_output=results,
        created_at=datetime.now(UTC),
    )
    assert inv.message_id == mid
    assert inv.tool_name == "web_search"
    assert inv.tool_input == '{"q": "hello"}'
    assert len(inv.tool_output) == 2
    assert inv.tool_output[0].title == "A"


def test_tool_invocation_frozen() -> None:
    inv = ToolInvocation(
        id=uuid.uuid4(),
        message_id=uuid.uuid4(),
        tool_name="t",
        tool_input="{}",
        tool_output=[],
        created_at=datetime.now(UTC),
    )
    with pytest.raises(AttributeError):
        inv.tool_name = "other"  # type: ignore[misc]


def test_message_default_tool_invocations() -> None:
    msg = Message(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        role="user",
        content="Hi",
        created_at=datetime.now(UTC),
    )
    assert msg.tool_invocations == []


def test_message_with_tool_invocations() -> None:
    mid = uuid.uuid4()
    inv = ToolInvocation(
        id=uuid.uuid4(),
        message_id=mid,
        tool_name="web_search",
        tool_input="q",
        tool_output=[SearchResult(title="x", snippet="y", url="https://z")],
        created_at=datetime.now(UTC),
    )
    msg = Message(
        id=mid,
        conversation_id=uuid.uuid4(),
        role="assistant",
        content="Here are results.",
        created_at=datetime.now(UTC),
        tool_invocations=[inv],
    )
    assert len(msg.tool_invocations) == 1
    assert msg.tool_invocations[0].tool_name == "web_search"
