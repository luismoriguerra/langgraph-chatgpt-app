# Data Model: ChatGPT Application

**Feature**: 001-chatgpt-app
**Date**: 2026-04-07

## Entity Relationship Diagram

```text
┌──────────────────────────┐
│      Conversation        │
├──────────────────────────┤
│ id          UUID (PK)    │
│ title       VARCHAR(100) │
│ created_at  TIMESTAMPTZ  │
│ updated_at  TIMESTAMPTZ  │
├──────────────────────────┤
│ 1:N → Message            │
└──────────────────────────┘
            │
            │ conversation_id (FK)
            ▼
┌──────────────────────────┐
│        Message           │
├──────────────────────────┤
│ id          UUID (PK)    │
│ conversation_id UUID(FK) │
│ role        VARCHAR(20)  │
│ content     TEXT         │
│ created_at  TIMESTAMPTZ  │
└──────────────────────────┘
```

## Entities

### Conversation

Represents a single chat thread.

| Column     | Type          | Constraints                        | Notes |
|------------|---------------|------------------------------------|-------|
| id         | UUID          | PK, default `gen_random_uuid()`    | Immutable |
| title      | VARCHAR(100)  | NOT NULL, default `'New conversation...'` | AI-generated after first message; fallback to truncated first message on failure |
| created_at | TIMESTAMPTZ   | NOT NULL, default `now()`          | Set once at creation |
| updated_at | TIMESTAMPTZ   | NOT NULL, default `now()`          | Updated when a new message is added |

**Identity & Uniqueness**: UUID primary key. No natural key (conversations have no user-facing unique identifier beyond the UUID).

**Lifecycle**:
- Created when the user sends the first message in a new chat.
- `updated_at` is refreshed each time a message is added.
- `title` transitions from the default placeholder to an AI-generated title asynchronously after the first message.
- Hard-deleted when the user confirms deletion (cascade deletes all messages).

**Indexes**:
- `ix_conversation_updated_at` on `updated_at DESC` — supports sidebar ordering (FR-004: most recently active first).

### Message

Represents a single exchange within a conversation.

| Column          | Type         | Constraints                        | Notes |
|-----------------|--------------|------------------------------------|-------|
| id              | UUID         | PK, default `gen_random_uuid()`    | Immutable |
| conversation_id | UUID         | FK → conversation.id, NOT NULL     | ON DELETE CASCADE |
| role            | VARCHAR(20)  | NOT NULL, CHECK IN ('user', 'assistant') | Enum-like constraint |
| content         | TEXT         | NOT NULL                           | Raw text; markdown rendered client-side for assistant messages |
| created_at      | TIMESTAMPTZ  | NOT NULL, default `now()`          | Chronological ordering |

**Identity & Uniqueness**: UUID primary key. Unique within its conversation by `(conversation_id, created_at)` for ordering.

**Lifecycle**:
- Created when a user sends a message (`role='user'`) or when the AI response stream completes (`role='assistant'`).
- Immutable after creation (no editing of messages in v1).
- Cascade-deleted when parent conversation is deleted.

**Indexes**:
- `ix_message_conversation_created` on `(conversation_id, created_at ASC)` — supports chronological loading of messages within a conversation (FR-008).

## Domain Entities (Python)

Domain entities are plain Python dataclasses with no framework imports (Principle I).

```python
@dataclass(frozen=True)
class Conversation:
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

@dataclass(frozen=True)
class Message:
    id: UUID
    conversation_id: UUID
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime
```

## Repository Protocols (Domain Layer)

```python
class ConversationRepository(Protocol):
    async def create(self, conversation: Conversation) -> Conversation: ...
    async def get_by_id(self, id: UUID) -> Conversation | None: ...
    async def list_recent(self, limit: int, offset: int) -> list[Conversation]: ...
    async def update_title(self, id: UUID, title: str) -> None: ...
    async def update_timestamp(self, id: UUID) -> None: ...
    async def delete(self, id: UUID) -> None: ...

class MessageRepository(Protocol):
    async def create(self, message: Message) -> Message: ...
    async def list_by_conversation(self, conversation_id: UUID) -> list[Message]: ...
```

## Validation Rules

- `Conversation.title`: max 100 characters, non-empty after generation.
- `Message.role`: must be exactly `"user"` or `"assistant"`.
- `Message.content`: non-empty, no whitespace-only messages (enforced at API layer per edge case).
- A conversation MUST have at least one message before it is persisted (empty new chats are discarded per US3 scenario 3).

## Data Volume Assumptions

- Single user, ~50 conversations (SC-004 target).
- Average conversation: ~20 messages.
- Total: ~1,000 messages in steady state.
- No pagination needed for v1 message loading (full conversation loaded at once).
- Sidebar pagination deferred; limit to most recent 50 conversations.
