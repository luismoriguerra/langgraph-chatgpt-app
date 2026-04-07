import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.domain.entities import Conversation
from app.infrastructure.database import get_db_session


def _make_app():
    from app.main import create_app

    app = create_app()
    mock_session = AsyncMock()

    async def override_session() -> AsyncGenerator:
        yield mock_session

    app.dependency_overrides[get_db_session] = override_session
    return app, mock_session


class TestChatStreamRoute:
    @pytest.mark.asyncio
    async def test_returns_streaming_response(self) -> None:
        app, _ = _make_app()
        conv_id = uuid.uuid4()
        now = datetime.now(UTC)
        conv = Conversation(id=conv_id, title="Test", created_at=now, updated_at=now)

        async def fake_send(**kwargs):
            yield {"type": "text-delta", "data": {"textDelta": "Hi"}}

        with (
            patch(
                "app.presentation.routes.chat.SqlAlchemyConversationRepository"
            ) as MockConvRepo,
            patch(
                "app.presentation.routes.chat.SqlAlchemyMessageRepository"
            ),
            patch(
                "app.presentation.routes.chat.SqlAlchemyToolInvocationRepository"
            ),
            patch("app.presentation.routes.chat.OpenAILLMService"),
            patch("app.presentation.routes.chat.use_cases") as mock_uc,
        ):
            MockConvRepo.return_value.get_by_id = AsyncMock(return_value=conv)
            mock_uc.send_message_with_agent = fake_send

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/conversations/{conv_id}/chat",
                    json={"message": "Hello"},
                )

            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sse_includes_all_event_types(self) -> None:
        app, _ = _make_app()
        conv_id = uuid.uuid4()
        now = datetime.now(UTC)
        conv = Conversation(id=conv_id, title="Test", created_at=now, updated_at=now)

        async def fake_send(**kwargs):
            yield {
                "type": "tool-start",
                "data": {"toolName": "duckduckgo_results_search", "toolInput": {"q": "test"}},
            }
            yield {"type": "tool-end", "data": {"toolName": "duckduckgo_results_search"}}
            yield {
                "type": "sources",
                "data": {
                    "sources": [
                        {"title": "T", "snippet": "S", "url": "https://example.com"}
                    ]
                },
            }
            yield {"type": "text-delta", "data": {"textDelta": "Answer"}}

        with (
            patch(
                "app.presentation.routes.chat.SqlAlchemyConversationRepository"
            ) as MockConvRepo,
            patch(
                "app.presentation.routes.chat.SqlAlchemyMessageRepository"
            ),
            patch(
                "app.presentation.routes.chat.SqlAlchemyToolInvocationRepository"
            ),
            patch("app.presentation.routes.chat.OpenAILLMService"),
            patch("app.presentation.routes.chat.use_cases") as mock_uc,
        ):
            MockConvRepo.return_value.get_by_id = AsyncMock(return_value=conv)
            mock_uc.send_message_with_agent = fake_send

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/conversations/{conv_id}/chat",
                    json={"message": "search test"},
                )

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

            tool_start = next(e for e in events if e["type"] == "tool-start")
            assert tool_start["toolName"] == "duckduckgo_results_search"

            sources = next(e for e in events if e["type"] == "sources")
            assert len(sources["sources"]) == 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_conversation(self) -> None:
        app, _ = _make_app()
        conv_id = uuid.uuid4()

        with (
            patch(
                "app.presentation.routes.chat.SqlAlchemyConversationRepository"
            ) as MockConvRepo,
            patch(
                "app.presentation.routes.chat.SqlAlchemyMessageRepository"
            ),
            patch(
                "app.presentation.routes.chat.SqlAlchemyToolInvocationRepository"
            ),
            patch("app.presentation.routes.chat.OpenAILLMService"),
        ):
            MockConvRepo.return_value.get_by_id = AsyncMock(return_value=None)

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/conversations/{conv_id}/chat",
                    json={"message": "Hello"},
                )

            assert resp.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_error_event_on_exception(self) -> None:
        app, _ = _make_app()
        conv_id = uuid.uuid4()
        now = datetime.now(UTC)
        conv = Conversation(id=conv_id, title="Test", created_at=now, updated_at=now)

        async def failing_send(**kwargs):
            raise RuntimeError("Something broke")
            yield  # noqa: RET503

        with (
            patch(
                "app.presentation.routes.chat.SqlAlchemyConversationRepository"
            ) as MockConvRepo,
            patch(
                "app.presentation.routes.chat.SqlAlchemyMessageRepository"
            ),
            patch(
                "app.presentation.routes.chat.SqlAlchemyToolInvocationRepository"
            ),
            patch("app.presentation.routes.chat.OpenAILLMService"),
            patch("app.presentation.routes.chat.use_cases") as mock_uc,
        ):
            MockConvRepo.return_value.get_by_id = AsyncMock(return_value=conv)
            mock_uc.send_message_with_agent = failing_send

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/conversations/{conv_id}/chat",
                    json={"message": "Hello"},
                )

            sse_lines = [
                line for line in resp.text.strip().split("\n\n") if line.startswith("data: ")
            ]
            events = [json.loads(line.removeprefix("data: ")) for line in sse_lines]
            types = [e["type"] for e in events]
            assert "error" in types

        app.dependency_overrides.clear()
