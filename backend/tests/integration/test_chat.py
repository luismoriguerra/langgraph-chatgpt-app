import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessageChunk


@pytest.mark.asyncio
async def test_chat_sse_stream_with_tool_events(client: AsyncClient) -> None:
    create_resp = await client.post("/api/conversations", json={"title": "Search Test"})
    assert create_resp.status_code == 201
    conv_id = create_resp.json()["id"]

    async def fake_agent_events(*args, **kwargs):
        yield {
            "event": "on_tool_start",
            "name": "duckduckgo_results_search",
            "data": {"input": {"query": "Python language"}},
            "run_id": "r1",
        }
        yield {
            "event": "on_tool_end",
            "name": "duckduckgo_results_search",
            "data": {
                "output": '[{"title": "Python.org", "snippet": "Welcome to Python", "link": "https://python.org"}]'
            },
            "run_id": "r1",
        }
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": AIMessageChunk(content="Python is a programming language.")},
            "run_id": "r2",
            "name": "ChatOpenAI",
        }

    mock_agent = MagicMock()
    mock_agent.astream_events = fake_agent_events

    with (
        patch("app.infrastructure.llm_service.build_chat_agent", return_value=mock_agent),
        patch(
            "app.infrastructure.llm_service.OpenAILLMService.generate_title",
            new_callable=AsyncMock,
            return_value="Python Question",
        ),
    ):
        resp = await client.post(
            f"/api/conversations/{conv_id}/chat",
            json={"message": "What is Python?"},
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    sse_lines = [
        line for line in resp.text.strip().split("\n\n") if line.startswith("data: ")
    ]
    events = [json.loads(line.removeprefix("data: ")) for line in sse_lines]
    types = [e["type"] for e in events]

    assert "tool-start" in types
    assert "tool-end" in types
    assert "sources" in types
    assert "text-delta" in types
    assert "finish" in types

    text_deltas = [e for e in events if e["type"] == "text-delta"]
    combined_text = "".join(e["textDelta"] for e in text_deltas)
    assert "Python" in combined_text


@pytest.mark.asyncio
async def test_chat_sse_text_only_response(client: AsyncClient) -> None:
    create_resp = await client.post("/api/conversations", json={"title": "Simple Chat"})
    conv_id = create_resp.json()["id"]

    async def fake_agent_events(*args, **kwargs):
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": AIMessageChunk(content="Hello!")},
            "run_id": "r1",
            "name": "ChatOpenAI",
        }

    mock_agent = MagicMock()
    mock_agent.astream_events = fake_agent_events

    with (
        patch("app.infrastructure.llm_service.build_chat_agent", return_value=mock_agent),
        patch(
            "app.infrastructure.llm_service.OpenAILLMService.generate_title",
            new_callable=AsyncMock,
            return_value="Greeting",
        ),
    ):
        resp = await client.post(
            f"/api/conversations/{conv_id}/chat",
            json={"message": "Hi there"},
        )

    sse_lines = [
        line for line in resp.text.strip().split("\n\n") if line.startswith("data: ")
    ]
    events = [json.loads(line.removeprefix("data: ")) for line in sse_lines]
    types = [e["type"] for e in events]

    assert "text-delta" in types
    assert "finish" in types
    assert "tool-start" not in types
