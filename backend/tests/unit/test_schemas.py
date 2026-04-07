import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.presentation.schemas import (
    CreateConversationRequest,
    MessageResponse,
    SearchResultResponse,
    SendMessageRequest,
    ToolInvocationResponse,
    UpdateConversationRequest,
)


def test_search_result_response() -> None:
    m = SearchResultResponse(title="T", snippet="S", url="https://example.com")
    assert m.title == "T"
    assert m.snippet == "S"
    assert m.url == "https://example.com"


def test_tool_invocation_response() -> None:
    iid = uuid.uuid4()
    now = datetime.now(UTC)
    out = [
        SearchResultResponse(title="A", snippet="a", url="https://a.test"),
        SearchResultResponse(title="B", snippet="b", url="https://b.test"),
    ]
    m = ToolInvocationResponse(
        id=iid,
        tool_name="web_search",
        tool_input='{"q": "hello"}',
        tool_output=out,
        created_at=now,
    )
    assert m.id == iid
    assert m.tool_name == "web_search"
    assert m.tool_input == '{"q": "hello"}'
    assert len(m.tool_output) == 2
    assert m.created_at == now


def test_message_response_with_tool_invocations() -> None:
    msg = MessageResponse(
        id=uuid.uuid4(),
        role="user",
        content="Hi",
        created_at=datetime.now(UTC),
    )
    assert msg.tool_invocations == []


def test_message_response_with_populated_invocations() -> None:
    mid = uuid.uuid4()
    inv = ToolInvocationResponse(
        id=uuid.uuid4(),
        tool_name="web_search",
        tool_input="q",
        tool_output=[SearchResultResponse(title="x", snippet="y", url="https://z")],
        created_at=datetime.now(UTC),
    )
    msg = MessageResponse(
        id=mid,
        role="assistant",
        content="Results below.",
        created_at=datetime.now(UTC),
        tool_invocations=[inv],
    )
    assert len(msg.tool_invocations) == 1
    assert msg.tool_invocations[0].tool_name == "web_search"
    assert msg.tool_invocations[0].tool_output[0].url == "https://z"


def test_send_message_request_valid() -> None:
    req = SendMessageRequest(message="Hello")
    assert req.message == "Hello"


def test_send_message_request_empty_rejected() -> None:
    with pytest.raises(ValidationError):
        SendMessageRequest(message="")


def test_send_message_request_too_long_rejected() -> None:
    with pytest.raises(ValidationError):
        SendMessageRequest(message="x" * 10001)


def test_create_conversation_request_default_title() -> None:
    req = CreateConversationRequest()
    assert req.title == "New conversation..."


def test_update_conversation_request_max_length() -> None:
    with pytest.raises(ValidationError):
        UpdateConversationRequest(title="x" * 101)
