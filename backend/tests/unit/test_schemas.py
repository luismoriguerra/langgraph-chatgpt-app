import pytest
from pydantic import ValidationError

from app.presentation.schemas import (
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    SendMessageRequest,
    UpdateConversationRequest,
)


class TestSendMessageRequest:
    def test_valid_message(self) -> None:
        req = SendMessageRequest(message="Hello")
        assert req.message == "Hello"

    def test_empty_message_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SendMessageRequest(message="")

    def test_max_length_enforced(self) -> None:
        long_msg = "a" * 10001
        with pytest.raises(ValidationError):
            SendMessageRequest(message=long_msg)

    def test_exactly_max_length_accepted(self) -> None:
        msg = "a" * 10000
        req = SendMessageRequest(message=msg)
        assert len(req.message) == 10000


class TestCreateConversationRequest:
    def test_default_title(self) -> None:
        req = CreateConversationRequest()
        assert req.title == "New conversation..."

    def test_custom_title(self) -> None:
        req = CreateConversationRequest(title="My Chat")
        assert req.title == "My Chat"


class TestUpdateConversationRequest:
    def test_valid_title(self) -> None:
        req = UpdateConversationRequest(title="Updated Title")
        assert req.title == "Updated Title"

    def test_title_max_length_enforced(self) -> None:
        with pytest.raises(ValidationError):
            UpdateConversationRequest(title="a" * 101)


class TestConversationResponse:
    def test_from_dict(self) -> None:
        data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Test",
            "created_at": "2026-04-07T10:00:00",
            "updated_at": "2026-04-07T10:00:00",
        }
        resp = ConversationResponse(**data)
        assert resp.title == "Test"


class TestConversationListResponse:
    def test_empty_list(self) -> None:
        resp = ConversationListResponse(conversations=[], total=0)
        assert resp.total == 0
        assert resp.conversations == []
