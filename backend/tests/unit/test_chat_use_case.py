import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases import send_message_with_agent
from app.domain.entities import Message, SearchResult, ToolInvocation


class TestSendMessageWithAgent:
    @pytest.mark.asyncio
    async def test_persists_user_message(
        self,
        make_conversation,
        make_message,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
        mock_llm_service,
    ) -> None:
        conv = make_conversation()
        mock_conversation_repo.get_by_id.return_value = conv
        user_msg = make_message(conversation_id=conv.id, role="user", content="Hi")
        mock_message_repo.create.return_value = user_msg
        mock_message_repo.list_by_conversation.return_value = [user_msg]

        events = []
        async for event in send_message_with_agent(
            conversation_id=conv.id,
            user_content="Hi",
            conv_repo=mock_conversation_repo,
            msg_repo=mock_message_repo,
            tool_repo=mock_tool_repo,
            llm_service=mock_llm_service,
        ):
            events.append(event)

        first_create_arg = mock_message_repo.create.call_args_list[0][0][0]
        assert first_create_arg.role == "user"
        assert first_create_arg.content == "Hi"

    @pytest.mark.asyncio
    async def test_yields_chat_events(
        self,
        make_conversation,
        make_message,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
        mock_llm_service,
    ) -> None:
        conv = make_conversation()
        mock_conversation_repo.get_by_id.return_value = conv
        user_msg = make_message(conversation_id=conv.id, role="user", content="Hi")
        mock_message_repo.create.return_value = user_msg
        mock_message_repo.list_by_conversation.return_value = [user_msg]

        events = []
        async for event in send_message_with_agent(
            conversation_id=conv.id,
            user_content="Hi",
            conv_repo=mock_conversation_repo,
            msg_repo=mock_message_repo,
            tool_repo=mock_tool_repo,
            llm_service=mock_llm_service,
        ):
            events.append(event)

        assert len(events) >= 1
        assert events[0]["type"] == "text-delta"
        assert events[0]["data"]["textDelta"] == "Hello from agent"

    @pytest.mark.asyncio
    async def test_persists_assistant_message_after_stream(
        self,
        make_conversation,
        make_message,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
        mock_llm_service,
    ) -> None:
        conv = make_conversation()
        mock_conversation_repo.get_by_id.return_value = conv
        user_msg = make_message(conversation_id=conv.id, role="user", content="Hi")
        mock_message_repo.create.return_value = user_msg
        mock_message_repo.list_by_conversation.return_value = [user_msg]

        async for _ in send_message_with_agent(
            conversation_id=conv.id,
            user_content="Hi",
            conv_repo=mock_conversation_repo,
            msg_repo=mock_message_repo,
            tool_repo=mock_tool_repo,
            llm_service=mock_llm_service,
        ):
            pass

        assert mock_message_repo.create.call_count == 2
        assistant_msg = mock_message_repo.create.call_args_list[1][0][0]
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "Hello from agent"

    @pytest.mark.asyncio
    async def test_persists_tool_invocations(
        self,
        make_conversation,
        make_message,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
    ) -> None:
        conv = make_conversation()
        mock_conversation_repo.get_by_id.return_value = conv
        user_msg = make_message(conversation_id=conv.id, role="user", content="Hi")
        mock_message_repo.create.return_value = user_msg
        mock_message_repo.list_by_conversation.return_value = [user_msg]

        llm = AsyncMock()

        async def stream_with_tools(*args, **kwargs):
            yield {
                "type": "tool-start",
                "data": {"toolName": "duckduckgo_results_search", "toolInput": {"query": "test"}},
            }
            yield {"type": "tool-end", "data": {"toolName": "duckduckgo_results_search"}}
            yield {
                "type": "sources",
                "data": {
                    "sources": [
                        {"title": "Result", "snippet": "A result", "url": "https://example.com"}
                    ]
                },
            }
            yield {"type": "text-delta", "data": {"textDelta": "Here are results"}}

        llm.stream_agent_chat = stream_with_tools
        llm.generate_title = AsyncMock(return_value="Test Title")

        async for _ in send_message_with_agent(
            conversation_id=conv.id,
            user_content="Hi",
            conv_repo=mock_conversation_repo,
            msg_repo=mock_message_repo,
            tool_repo=mock_tool_repo,
            llm_service=llm,
        ):
            pass

        assert mock_tool_repo.create.call_count == 1
        tool_inv = mock_tool_repo.create.call_args_list[0][0][0]
        assert tool_inv.tool_name == "duckduckgo_results_search"
        assert len(tool_inv.tool_output) == 1
        assert tool_inv.tool_output[0].url == "https://example.com"

    @pytest.mark.asyncio
    async def test_generates_title_on_first_message(
        self,
        make_conversation,
        make_message,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
        mock_llm_service,
    ) -> None:
        conv = make_conversation()
        mock_conversation_repo.get_by_id.return_value = conv
        user_msg = make_message(conversation_id=conv.id, role="user", content="Hi")
        mock_message_repo.create.return_value = user_msg
        mock_message_repo.list_by_conversation.return_value = [user_msg]

        async for _ in send_message_with_agent(
            conversation_id=conv.id,
            user_content="Hi",
            conv_repo=mock_conversation_repo,
            msg_repo=mock_message_repo,
            tool_repo=mock_tool_repo,
            llm_service=mock_llm_service,
        ):
            pass

        mock_llm_service.generate_title.assert_awaited_once_with("Hi")
        mock_conversation_repo.update_title.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_for_unknown_conversation(
        self,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
        mock_llm_service,
    ) -> None:
        mock_conversation_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            async for _ in send_message_with_agent(
                conversation_id=uuid.uuid4(),
                user_content="Hi",
                conv_repo=mock_conversation_repo,
                msg_repo=mock_message_repo,
                tool_repo=mock_tool_repo,
                llm_service=mock_llm_service,
            ):
                pass

    @pytest.mark.asyncio
    async def test_skips_title_on_subsequent_messages(
        self,
        make_conversation,
        make_message,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
        mock_llm_service,
    ) -> None:
        conv = make_conversation()
        mock_conversation_repo.get_by_id.return_value = conv
        user_msg = make_message(conversation_id=conv.id, role="user", content="Hello again")
        prev_msg = make_message(conversation_id=conv.id, role="user", content="First msg")
        prev_reply = make_message(conversation_id=conv.id, role="assistant", content="Reply")
        mock_message_repo.create.return_value = user_msg
        mock_message_repo.list_by_conversation.return_value = [prev_msg, prev_reply, user_msg]

        async for _ in send_message_with_agent(
            conversation_id=conv.id,
            user_content="Hello again",
            conv_repo=mock_conversation_repo,
            msg_repo=mock_message_repo,
            tool_repo=mock_tool_repo,
            llm_service=mock_llm_service,
        ):
            pass

        mock_llm_service.generate_title.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_passes_full_history_including_tool_invocations_to_stream_agent_chat(
        self,
        make_conversation,
        make_message,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
        mock_llm_service,
    ) -> None:
        conv = make_conversation()
        mock_conversation_repo.get_by_id.return_value = conv
        prev_user = make_message(conversation_id=conv.id, role="user", content="Search for cats")
        assistant_id = uuid.uuid4()
        now = datetime.now(UTC)
        tool_inv = ToolInvocation(
            id=uuid.uuid4(),
            message_id=assistant_id,
            tool_name="duckduckgo_results_search",
            tool_input='{"query":"cats"}',
            tool_output=[SearchResult(title="R", snippet="S", url="https://example.com")],
            created_at=now,
        )
        prev_assistant = Message(
            id=assistant_id,
            conversation_id=conv.id,
            role="assistant",
            content="Here are results about cats",
            created_at=now,
            tool_invocations=[tool_inv],
        )
        new_user = make_message(conversation_id=conv.id, role="user", content="What about dogs?")
        mock_message_repo.create.return_value = new_user
        full_history = [prev_user, prev_assistant, new_user]
        mock_message_repo.list_by_conversation.return_value = full_history
        mock_tool_repo.list_by_conversation.return_value = [tool_inv]

        captured: list[list[Message]] = []

        async def capture_stream(history: list[Message]):
            captured.append(history)
            yield {"type": "text-delta", "data": {"textDelta": "ok"}}

        mock_llm_service.stream_agent_chat = capture_stream

        async for _ in send_message_with_agent(
            conversation_id=conv.id,
            user_content="What about dogs?",
            conv_repo=mock_conversation_repo,
            msg_repo=mock_message_repo,
            tool_repo=mock_tool_repo,
            llm_service=mock_llm_service,
        ):
            pass

        assert len(captured) == 1
        hist = captured[0]
        assert len(hist) == 3
        assert hist[0].content == "Search for cats"
        assert hist[0].role == "user"
        assert hist[1].role == "assistant"
        assert len(hist[1].tool_invocations) == 1
        assert hist[1].tool_invocations[0].tool_name == "duckduckgo_results_search"
        assert hist[2].content == "What about dogs?"
        assert hist[2].role == "user"

    @pytest.mark.asyncio
    async def test_persists_tool_result_from_tool_result_event(
        self,
        make_conversation,
        make_message,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
    ) -> None:
        conv = make_conversation()
        mock_conversation_repo.get_by_id.return_value = conv
        user_msg = make_message(conversation_id=conv.id, role="user", content="What is 5+3?")
        mock_message_repo.create.return_value = user_msg
        mock_message_repo.list_by_conversation.return_value = [user_msg]

        llm = AsyncMock()

        async def stream_with_calculate(*args, **kwargs):
            yield {
                "type": "tool-start",
                "data": {"toolName": "calculate", "toolInput": "5+3"},
            }
            yield {"type": "tool-end", "data": {"toolName": "calculate"}}
            yield {"type": "sources", "data": {"sources": []}}
            yield {
                "type": "tool-result",
                "data": {"toolName": "calculate", "toolInput": "5+3", "result": "8"},
            }
            yield {"type": "text-delta", "data": {"textDelta": "The answer is 8"}}

        llm.stream_agent_chat = stream_with_calculate
        llm.generate_title = AsyncMock(return_value="Math Question")

        async for _ in send_message_with_agent(
            conversation_id=conv.id,
            user_content="What is 5+3?",
            conv_repo=mock_conversation_repo,
            msg_repo=mock_message_repo,
            tool_repo=mock_tool_repo,
            llm_service=llm,
        ):
            pass

        assert mock_tool_repo.create.call_count == 1
        tool_inv = mock_tool_repo.create.call_args_list[0][0][0]
        assert tool_inv.tool_name == "calculate"
        assert tool_inv.tool_result == "8"
        assert tool_inv.tool_output == []

    @pytest.mark.asyncio
    async def test_stream_agent_chat_receives_prior_messages_in_chronological_order(
        self,
        make_conversation,
        make_message,
        mock_conversation_repo,
        mock_message_repo,
        mock_tool_repo,
        mock_llm_service,
    ) -> None:
        conv = make_conversation()
        mock_conversation_repo.get_by_id.return_value = conv
        m1 = make_message(conversation_id=conv.id, role="user", content="first")
        m2 = make_message(conversation_id=conv.id, role="assistant", content="second")
        m3 = make_message(conversation_id=conv.id, role="user", content="third")
        mock_message_repo.create.return_value = m3
        full_history = [m1, m2, m3]
        mock_message_repo.list_by_conversation.return_value = full_history
        mock_tool_repo.list_by_conversation.return_value = []

        seen_orders: list[list[str]] = []

        async def capture_stream(history: list[Message]):
            seen_orders.append([m.content for m in history])
            yield {"type": "text-delta", "data": {"textDelta": "x"}}

        mock_llm_service.stream_agent_chat = capture_stream

        async for _ in send_message_with_agent(
            conversation_id=conv.id,
            user_content="third",
            conv_repo=mock_conversation_repo,
            msg_repo=mock_message_repo,
            tool_repo=mock_tool_repo,
            llm_service=mock_llm_service,
        ):
            pass

        assert seen_orders == [["first", "second", "third"]]
