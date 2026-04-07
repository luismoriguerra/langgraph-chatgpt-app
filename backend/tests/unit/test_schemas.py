import uuid
from datetime import UTC, datetime

from app.presentation.schemas import (
    MessageResponse,
    SearchResultResponse,
    ToolInvocationResponse,
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
