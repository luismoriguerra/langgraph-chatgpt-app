# Data Model: Web Search Tool

**Branch**: `002-web-search-tool` | **Date**: 2026-04-07

## Existing Entities (Unchanged)

### Conversation

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| title | String(100) | Auto-generated |
| created_at | DateTime | Server default |
| updated_at | DateTime | Server default, on update |

### Message

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| conversation_id | UUID | FK → conversations.id |
| role | String(20) | "user" or "assistant" |
| content | Text | Message body |
| created_at | DateTime | Server default |

## New Entity

### ToolInvocation

Stores a record of each tool call the AI made during a message turn. Linked to the assistant message that resulted from the tool use.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| message_id | UUID | FK → messages.id, ON DELETE CASCADE |
| tool_name | String(50) | e.g., "duckduckgo_search" |
| tool_input | Text | The search query string |
| tool_output | JSON | Structured: `[{ title, snippet, url }]` |
| created_at | DateTime | Server default |

**Indexes**:
- `ix_tool_invocation_message_id` on `message_id` (for loading invocations when fetching a conversation)

**Relationships**:
- `Message` 1 → N `ToolInvocation` (one assistant message may have up to 3 tool calls)
- Cascade delete: deleting a message deletes its tool invocations
- Cascade from conversation: deleting a conversation cascades to messages, then to tool invocations

## Domain Entity Changes

### New: `ToolInvocation` dataclass

```python
@dataclass(frozen=True)
class ToolInvocation:
    id: UUID
    message_id: UUID
    tool_name: str
    tool_input: str
    tool_output: list[SearchResult]
    created_at: datetime
```

### New: `SearchResult` dataclass

```python
@dataclass(frozen=True)
class SearchResult:
    title: str
    snippet: str
    url: str
```

### Updated: `Message` entity

Add an optional `tool_invocations` field for read-path convenience:

```python
@dataclass(frozen=True)
class Message:
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
    tool_invocations: list[ToolInvocation] = field(default_factory=list)
```

## Port Changes

### New: `ToolInvocationRepository` protocol

```python
class ToolInvocationRepository(Protocol):
    async def create(self, invocation: ToolInvocation) -> ToolInvocation: ...
    async def list_by_message(self, message_id: UUID) -> list[ToolInvocation]: ...
    async def list_by_conversation(self, conversation_id: UUID) -> list[ToolInvocation]: ...
```

### Updated: `LLMService` protocol

The existing `stream_chat` method returns `AsyncIterator[str]` (token strings). For the agent, the service needs to yield structured events instead:

```python
class ChatEvent(TypedDict):
    type: str           # "text-delta" | "tool-start" | "tool-end" | "sources"
    data: dict[str, Any]

class LLMService(Protocol):
    def stream_chat(
        self, messages: list[Message], system_prompt: str = ""
    ) -> AsyncIterator[str]: ...

    def stream_agent_chat(
        self, messages: list[Message], system_prompt: str = ""
    ) -> AsyncIterator[ChatEvent]: ...

    async def generate_title(self, first_message: str) -> str: ...
```

## Migration

An Alembic migration will:
1. Create the `tool_invocations` table
2. Add the FK index on `message_id`

Both `upgrade()` and `downgrade()` functions will be provided (downgrade drops the table).
