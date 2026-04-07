import json
from typing import TypedDict

import structlog
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.domain.entities import Message

logger = structlog.get_logger()

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

    return create_react_agent(llm, [search_tool])
