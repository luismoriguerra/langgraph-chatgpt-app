import ast
import json
import math
from typing import TypedDict

import structlog
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.domain.entities import Message

logger = structlog.get_logger()

_SAFE_NAMES: dict[str, object] = {
    k: v for k, v in math.__dict__.items() if not k.startswith("_")
}
_SAFE_NAMES.update({"abs": abs, "round": round, "min": min, "max": max})

SYSTEM_PROMPT = "You are a helpful AI assistant. Be concise and clear in your responses."


class ChatState(TypedDict):
    messages: list[BaseMessage]
    system_prompt: str


class TitleState(TypedDict):
    first_message: str
    title: str


def prepare_messages(conversation_messages: list[Message], system_prompt: str = "") -> ChatState:
    lc_messages: list[BaseMessage] = []

    prompt = system_prompt or SYSTEM_PROMPT
    lc_messages.append(SystemMessage(content=prompt))

    for msg in conversation_messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        else:
            lc_messages.append(AIMessage(content=msg.content))

    return ChatState(messages=lc_messages, system_prompt=prompt)


def safe_eval(expression: str) -> str:
    """Evaluate a mathematical expression safely and return the string result."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute)):
                raise ValueError(f"Unsafe expression: {expression}")
        result = eval(  # noqa: S307
            compile(tree, "<expr>", "eval"),
            {"__builtins__": {}},
            _SAFE_NAMES,
        )
        if isinstance(result, float):
            rounded = round(result, 10)
            formatted = f"{rounded:.10f}".rstrip("0").rstrip(".")
            if "." in formatted:
                return formatted
            return formatted
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero"
    except (ValueError, SyntaxError, TypeError, NameError) as exc:
        return f"Error: {exc}"


def build_chat_agent(llm: ChatOpenAI, max_search_calls: int = 3):
    ddg = DuckDuckGoSearchResults(num_results=4)
    search_calls = 0

    def _limited_search(query: str) -> str:
        nonlocal search_calls
        if search_calls >= max_search_calls:
            logger.warning("web_search.limit_reached", max_search_calls=max_search_calls)
            return json.dumps([])
        search_calls += 1
        try:
            return str(ddg.invoke(query))
        except (TimeoutError, ConnectionError, OSError) as exc:
            logger.warning(
                "web_search.invoke_failed",
                exc_type=type(exc).__name__,
                error=str(exc),
            )
            return json.dumps([])
        except Exception as exc:
            logger.warning(
                "web_search.invoke_failed",
                exc_type=type(exc).__name__,
                error=str(exc),
            )
            return json.dumps([])

    search_tool = StructuredTool.from_function(
        name="web_search",
        description="Search the public web for current information and return result snippets.",
        func=_limited_search,
    )

    calculate_tool = StructuredTool.from_function(
        name="calculate",
        description=(
            "Evaluate a mathematical expression and return the numeric result. "
            "Supports arithmetic (+, -, *, /, **, %), math functions (sqrt, sin, cos, log, etc.), "
            "and constants (pi, e). Pass the expression as a string, e.g. 'sqrt(144) + 3**2'."
        ),
        func=safe_eval,
    )

    return create_react_agent(llm, [search_tool, calculate_tool])
