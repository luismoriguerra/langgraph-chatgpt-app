from unittest.mock import MagicMock

from langchain_openai import ChatOpenAI

from app.application.chat_graph import build_chat_agent


class TestBuildChatAgent:
    def test_returns_compiled_graph_with_astream_events(self) -> None:
        mock_llm = MagicMock(spec=ChatOpenAI)
        agent = build_chat_agent(mock_llm)
        assert hasattr(agent, "astream_events")

    def test_returns_compiled_graph_with_invoke(self) -> None:
        mock_llm = MagicMock(spec=ChatOpenAI)
        agent = build_chat_agent(mock_llm)
        assert hasattr(agent, "ainvoke")

    def test_accepts_chat_openai_model(self) -> None:
        mock_llm = MagicMock(spec=ChatOpenAI)
        agent = build_chat_agent(mock_llm)
        assert agent is not None

    def test_custom_max_search_calls(self) -> None:
        mock_llm = MagicMock(spec=ChatOpenAI)
        agent = build_chat_agent(mock_llm, max_search_calls=5)
        assert agent is not None
