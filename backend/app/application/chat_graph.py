from typing import TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.domain.entities import Message

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
