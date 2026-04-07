from collections.abc import AsyncIterator

import structlog
from langchain_core.messages import AIMessageChunk
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
            api_key=self._api_key,  # type: ignore[arg-type]
            streaming=True,
        )

    async def stream_chat(
        self, messages: list[Message], system_prompt: str = ""
    ) -> AsyncIterator[str]:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        lc_messages: list[HumanMessage | AIMessage | SystemMessage] = []
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))

        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            else:
                lc_messages.append(AIMessage(content=msg.content))

        logger.info("llm.stream_chat.start", model=self._model, message_count=len(lc_messages))

        async for chunk in self._llm.astream(lc_messages):
            if isinstance(chunk, AIMessageChunk) and isinstance(chunk.content, str):
                yield chunk.content

    async def generate_title(self, first_message: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        prompt_messages = [
            SystemMessage(
                content=(
                    "Generate a concise title (maximum 60 characters) for a conversation "
                    "that starts with the following message. Return ONLY the title, no quotes."
                )
            ),
            HumanMessage(content=first_message),
        ]

        logger.info("llm.generate_title.start", model=self._model)
        response = await self._llm.ainvoke(prompt_messages)
        title = str(response.content).strip()[:60]
        logger.info("llm.generate_title.done", title=title)
        return title
