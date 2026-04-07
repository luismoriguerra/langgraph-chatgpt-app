from unittest.mock import MagicMock

import pytest
from langchain_openai import ChatOpenAI

from app.application.chat_graph import build_chat_agent, safe_eval


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

    def test_agent_has_both_search_and_calculate_tools(self) -> None:
        mock_llm = MagicMock(spec=ChatOpenAI)
        agent = build_chat_agent(mock_llm)
        node_names = set(agent.get_graph().nodes.keys())
        assert "tools" in node_names


class TestSafeEval:
    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            ("2 + 3", "5"),
            ("10 - 4", "6"),
            ("125 * 8", "1000"),
            ("100 / 4", "25"),
            ("7 + 3 * 2", "13"),
        ],
    )
    def test_basic_arithmetic(self, expression: str, expected: str) -> None:
        assert safe_eval(expression) == expected

    def test_division_by_zero(self) -> None:
        result = safe_eval("5 / 0")
        assert result.startswith("Error:")
        assert "division by zero" in result

    def test_unsafe_import_expression(self) -> None:
        result = safe_eval("__import__('os').system('ls')")
        assert result.startswith("Error:")

    def test_unsafe_attribute_access(self) -> None:
        result = safe_eval("().__class__.__bases__")
        assert result.startswith("Error:")

    def test_invalid_syntax(self) -> None:
        result = safe_eval("2 +* 3")
        assert result.startswith("Error:")

    def test_unknown_name(self) -> None:
        result = safe_eval("abc + xyz")
        assert result.startswith("Error:")

    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            ("(50 + 30) * 2 - 15", "145"),
            ("2 ** 10", "1024"),
            ("sqrt(144)", "12"),
            ("15 % 4", "3"),
            ("abs(-42)", "42"),
        ],
    )
    def test_complex_expressions(self, expression: str, expected: str) -> None:
        assert safe_eval(expression) == expected

    def test_math_functions(self) -> None:
        result = safe_eval("sqrt(144) + 3**2")
        assert result == "21"

    def test_pi_constant(self) -> None:
        result = safe_eval("pi")
        assert result.startswith("3.14159")

    def test_floating_point_precision(self) -> None:
        result = safe_eval("0.1 + 0.2")
        assert result == "0.3"

    def test_trailing_zeros_stripped(self) -> None:
        result = safe_eval("1.0 + 0.5")
        assert result == "1.5"

    def test_integer_result_no_decimal(self) -> None:
        result = safe_eval("2 + 3")
        assert result == "5"
        assert "." not in result
