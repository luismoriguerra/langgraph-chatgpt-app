from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SearchResultResponse(BaseModel):
    title: str
    snippet: str
    url: str

    model_config = {"from_attributes": True}


class ToolInvocationResponse(BaseModel):
    id: UUID
    tool_name: str
    tool_input: str
    tool_output: list[SearchResultResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    tool_invocations: list[ToolInvocationResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse]


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int


class CreateConversationRequest(BaseModel):
    title: str = "New conversation..."


class UpdateConversationRequest(BaseModel):
    title: str = Field(..., max_length=100)


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
