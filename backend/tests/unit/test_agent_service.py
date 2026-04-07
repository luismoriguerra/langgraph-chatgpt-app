import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessageChunk

from app.domain.entities import Message
from app.infrastructure.llm_service import OpenAILLMService, _parse_search_results


@pytest.fixture
def llm_service():
    with patch.object(OpenAILLMService, "__init__", lambda self: None):
        svc = OpenAILLMService.__new__(OpenAILLMService)
        svc._model = "test-model"
        svc._api_key = "test-key"
        svc._llm = MagicMock()
        return svc


@pytest.fixture
def user_message():
    return Message(
        id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        role="user",
        content="What is Python?",
        created_at=datetime.now(UTC),
    )


class TestStreamAgentChat:
    @pytest.mark.asyncio
    async def test_yields_text_delta_events(
        self, llm_service: OpenAILLMService, user_message: Message
    ) -> None:
        async def fake_events(*args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Hello")},
                "run_id": "r1",
                "name": "ChatOpenAI",
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content=" world")},
                "run_id": "r1",
                "name": "ChatOpenAI",
            }

        mock_agent = MagicMock()
        mock_agent.astream_events = fake_events

        with patch(
            "app.infrastructure.llm_service.build_chat_agent", return_value=mock_agent
        ):
            events = [e async for e in llm_service.stream_agent_chat([user_message])]

        assert len(events) == 2
        assert events[0]["type"] == "text-delta"
        assert events[0]["data"]["textDelta"] == "Hello"
        assert events[1]["data"]["textDelta"] == " world"

    @pytest.mark.asyncio
    async def test_yields_tool_events(
        self, llm_service: OpenAILLMService, user_message: Message
    ) -> None:
        async def fake_events(*args, **kwargs):
            yield {
                "event": "on_tool_start",
                "name": "duckduckgo_results_search",
                "data": {"input": {"query": "Python"}},
                "run_id": "r1",
            }
            yield {
                "event": "on_tool_end",
                "name": "duckduckgo_results_search",
                "data": {
                    "output": '[{"title": "Python.org", "snippet": "Welcome", "link": "https://python.org"}]'
                },
                "run_id": "r1",
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Python is great")},
                "run_id": "r2",
                "name": "ChatOpenAI",
            }

        mock_agent = MagicMock()
        mock_agent.astream_events = fake_events

        with patch(
            "app.infrastructure.llm_service.build_chat_agent", return_value=mock_agent
        ):
            events = [e async for e in llm_service.stream_agent_chat([user_message])]

        types = [e["type"] for e in events]
        assert "tool-start" in types
        assert "tool-end" in types
        assert "sources" in types
        assert "text-delta" in types

        tool_start = next(e for e in events if e["type"] == "tool-start")
        assert tool_start["data"]["toolName"] == "duckduckgo_results_search"

        sources_event = next(e for e in events if e["type"] == "sources")
        assert len(sources_event["data"]["sources"]) == 1
        assert sources_event["data"]["sources"][0]["url"] == "https://python.org"

    @pytest.mark.asyncio
    async def test_skips_empty_content_chunks(
        self, llm_service: OpenAILLMService, user_message: Message
    ) -> None:
        async def fake_events(*args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="")},
                "run_id": "r1",
                "name": "ChatOpenAI",
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Real text")},
                "run_id": "r1",
                "name": "ChatOpenAI",
            }

        mock_agent = MagicMock()
        mock_agent.astream_events = fake_events

        with patch(
            "app.infrastructure.llm_service.build_chat_agent", return_value=mock_agent
        ):
            events = [e async for e in llm_service.stream_agent_chat([user_message])]

        assert len(events) == 1
        assert events[0]["data"]["textDelta"] == "Real text"

    @pytest.mark.asyncio
    async def test_handles_search_failure_gracefully(
        self, llm_service: OpenAILLMService, user_message: Message
    ) -> None:
        async def fake_events(*args, **kwargs):
            raise RuntimeError("Search API down")
            yield  # noqa: RET503

        mock_agent = MagicMock()
        mock_agent.astream_events = fake_events

        with patch(
            "app.infrastructure.llm_service.build_chat_agent", return_value=mock_agent
        ):
            events = [e async for e in llm_service.stream_agent_chat([user_message])]

        assert events == []

    @pytest.mark.asyncio
    async def test_respects_max_tool_calls(
        self, llm_service: OpenAILLMService, user_message: Message
    ) -> None:
        async def fake_events(*args, **kwargs):
            for i in range(5):
                yield {
                    "event": "on_tool_start",
                    "name": "duckduckgo_results_search",
                    "data": {"input": {"query": f"search {i}"}},
                    "run_id": f"r{i}",
                }
                yield {
                    "event": "on_tool_end",
                    "name": "duckduckgo_results_search",
                    "data": {"output": "[]"},
                    "run_id": f"r{i}",
                }

        mock_agent = MagicMock()
        mock_agent.astream_events = fake_events

        with patch(
            "app.infrastructure.llm_service.build_chat_agent", return_value=mock_agent
        ):
            events = [e async for e in llm_service.stream_agent_chat([user_message])]

        tool_starts = [e for e in events if e["type"] == "tool-start"]
        assert len(tool_starts) <= 3

    @pytest.mark.asyncio
    async def test_on_tool_error_yields_end_and_empty_sources(
        self, llm_service: OpenAILLMService, user_message: Message
    ) -> None:
        async def fake_events(*args, **kwargs):
            yield {
                "event": "on_tool_start",
                "name": "web_search",
                "data": {"input": {"query": "news"}},
                "run_id": "r1",
            }
            yield {
                "event": "on_tool_error",
                "name": "web_search",
                "data": {"error": RuntimeError("ddg down"), "input": {"query": "news"}},
                "run_id": "r1",
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": AIMessageChunk(content="Fallback answer.")},
                "run_id": "r2",
                "name": "ChatOpenAI",
            }

        mock_agent = MagicMock()
        mock_agent.astream_events = fake_events

        with patch(
            "app.infrastructure.llm_service.build_chat_agent", return_value=mock_agent
        ):
            events = [e async for e in llm_service.stream_agent_chat([user_message])]

        types = [e["type"] for e in events]
        assert "tool-start" in types
        assert "tool-end" in types
        assert "sources" in types
        assert "text-delta" in types
        sources_ev = next(e for e in events if e["type"] == "sources")
        assert sources_ev["data"]["sources"] == []


class TestParseSearchResults:
    def test_parses_json_array(self) -> None:
        raw = '[{"title": "A", "snippet": "a", "link": "https://a.com"}]'
        result = _parse_search_results(raw)
        assert len(result) == 1
        assert result[0]["title"] == "A"
        assert result[0]["url"] == "https://a.com"

    def test_parses_bracket_format(self) -> None:
        raw = "[snippet: some text, title: Some Title, link: https://example.com]"
        result = _parse_search_results(raw)
        assert len(result) == 1
        assert result[0]["title"] == "Some Title"
        assert result[0]["snippet"] == "some text"

    def test_returns_empty_on_invalid_input(self) -> None:
        result = _parse_search_results("not parseable at all")
        assert result == []

    def test_handles_json_with_href_key(self) -> None:
        raw = '[{"title": "B", "body": "b text", "href": "https://b.com"}]'
        result = _parse_search_results(raw)
        assert result[0]["snippet"] == "b text"
        assert result[0]["url"] == "https://b.com"
