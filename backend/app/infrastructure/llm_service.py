import json
import re
import time
from collections.abc import AsyncIterator

import structlog
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.application.chat_graph import SYSTEM_PROMPT, build_chat_agent
from app.config import settings
from app.domain.entities import Message
from app.domain.ports import ChatEvent  # used as type annotation only

logger = structlog.get_logger()


def _tool_input_query(tool_input: object) -> str:
    if isinstance(tool_input, dict):
        q = tool_input.get("query")
        if q is not None:
            return str(q)
        inner = tool_input.get("input")
        if inner is not None:
            return str(inner)
        return str(tool_input)
    return str(tool_input)


def _parse_search_results(raw_output: str) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    try:
        parsed = json.loads(raw_output)
        if isinstance(parsed, list):
            for item in parsed:
                sources.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", item.get("body", "")),
                    "url": item.get("link", item.get("href", "")),
                })
            return sources
    except (json.JSONDecodeError, TypeError):
        pass

    pattern = r"\[snippet:\s*(.*?),\s*title:\s*(.*?),\s*link:\s*(.*?)\]"
    matches = re.findall(pattern, raw_output)
    for snippet, title, link in matches:
        sources.append({
            "title": title.strip(),
            "snippet": snippet.strip(),
            "url": link.strip(),
        })
    return sources


class OpenAILLMService:
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self._model = model or settings.llm_model
        self._api_key = api_key or settings.openai_api_key
        self._llm = ChatOpenAI(
            model=self._model,
            api_key=self._api_key,
            streaming=True,
        )

    async def stream_chat(
        self, messages: list[Message], system_prompt: str = ""
    ) -> AsyncIterator[str]:
        lc_messages: list[HumanMessage | AIMessage | SystemMessage] = []
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))

        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            else:
                lc_messages.append(AIMessage(content=msg.content))

        start = time.monotonic()
        token_count = 0
        logger.info(
            "llm.stream_chat.start",
            model=self._model,
            message_count=len(lc_messages),
        )

        async for chunk in self._llm.astream(lc_messages):
            if isinstance(chunk, AIMessageChunk) and isinstance(chunk.content, str):
                token_count += 1
                yield chunk.content

        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "llm.stream_chat.done",
            model=self._model,
            token_count=token_count,
            elapsed_ms=elapsed_ms,
        )

    async def stream_agent_chat(
        self, messages: list[Message], system_prompt: str = ""
    ) -> AsyncIterator[ChatEvent]:
        lc_messages: list[HumanMessage | AIMessage | SystemMessage] = []
        prompt = system_prompt or SYSTEM_PROMPT
        lc_messages.append(SystemMessage(content=prompt))

        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            else:
                lc_messages.append(AIMessage(content=msg.content))

        agent = build_chat_agent(self._llm)
        max_search_calls = 3
        tool_call_count = 0
        token_count = 0
        tool_run_started: dict[str, float] = {}

        start = time.monotonic()
        logger.info(
            "llm.stream_agent_chat.start",
            model=self._model,
            message_count=len(lc_messages),
        )

        try:
            async for event in agent.astream_events(
                {"messages": lc_messages}, version="v2"
            ):
                kind = event["event"]

                if kind == "on_tool_start" and event.get("name"):
                    tool_call_count += 1
                    if tool_call_count > max_search_calls:
                        logger.warning(
                            "llm.stream_agent_chat.max_tools_reached",
                            count=tool_call_count,
                        )
                        break
                    run_id = str(event.get("run_id", ""))
                    tool_run_started[run_id] = time.monotonic()
                    inp = event["data"].get("input", {})
                    q = _tool_input_query(inp)
                    logger.info(
                        "llm.stream_agent_chat.tool_invocation",
                        phase="start",
                        tool_name=event["name"],
                        query=q,
                    )
                    yield {
                        "type": "tool-start",
                        "data": {
                            "toolName": event["name"],
                            "toolInput": q,
                        },
                    }

                elif kind == "on_tool_error" and event.get("name"):
                    run_id = str(event.get("run_id", ""))
                    t0 = tool_run_started.pop(run_id, None)
                    latency_ms = (
                        int((time.monotonic() - t0) * 1000) if t0 is not None else None
                    )
                    err = event["data"].get("error")
                    err_s = repr(err) if err is not None else "unknown"
                    inp = event["data"].get("input", {})
                    q = _tool_input_query(inp)
                    logger.warning(
                        "llm.stream_agent_chat.tool_invocation",
                        phase="error",
                        tool_name=event["name"],
                        latency_ms=latency_ms,
                        error=err_s,
                    )
                    yield {
                        "type": "tool-end",
                        "data": {"toolName": event["name"]},
                    }
                    yield {
                        "type": "sources",
                        "data": {"sources": []},
                    }
                    yield {
                        "type": "tool-result",
                        "data": {
                            "toolName": event["name"],
                            "toolInput": q,
                            "result": f"Error: {err_s}",
                        },
                    }

                elif kind == "on_tool_end" and event.get("name"):
                    run_id = str(event.get("run_id", ""))
                    t0 = tool_run_started.pop(run_id, None)
                    latency_ms = (
                        int((time.monotonic() - t0) * 1000) if t0 is not None else None
                    )
                    logger.info(
                        "llm.stream_agent_chat.tool_invocation",
                        phase="end",
                        tool_name=event["name"],
                        latency_ms=latency_ms,
                    )
                    raw_output = str(event["data"].get("output", ""))
                    sources = _parse_search_results(raw_output)
                    inp = event["data"].get("input", {})
                    q = _tool_input_query(inp)
                    yield {
                        "type": "tool-end",
                        "data": {"toolName": event["name"]},
                    }
                    yield {
                        "type": "sources",
                        "data": {"sources": sources},
                    }
                    yield {
                        "type": "tool-result",
                        "data": {
                            "toolName": event["name"],
                            "toolInput": q,
                            "result": raw_output,
                        },
                    }

                elif kind == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk and isinstance(chunk.content, str) and chunk.content:
                        token_count += 1
                        yield {
                            "type": "text-delta",
                            "data": {"textDelta": chunk.content},
                        }

        except (ConnectionError, TimeoutError, OSError):
            logger.exception("llm.stream_agent_chat.transport_error")
        except Exception:
            logger.exception("llm.stream_agent_chat.error")

        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "llm.stream_agent_chat.done",
            model=self._model,
            tool_calls=tool_call_count,
            token_count=token_count,
            elapsed_ms=elapsed_ms,
        )

    async def generate_title(self, first_message: str) -> str:
        prompt_messages = [
            SystemMessage(
                content=(
                    "Generate a concise title (maximum 60 characters) for a conversation "
                    "that starts with the following message. Return ONLY the title, no quotes."
                )
            ),
            HumanMessage(content=first_message),
        ]

        start = time.monotonic()
        logger.info("llm.generate_title.start", model=self._model)
        response = await self._llm.ainvoke(prompt_messages)
        title = str(response.content).strip()[:60]
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "llm.generate_title.done",
            title=title,
            elapsed_ms=elapsed_ms,
        )
        return title
