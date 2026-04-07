import time
from collections.abc import AsyncIterator

import structlog
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.domain.entities import Message

logger = structlog.get_logger()


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
