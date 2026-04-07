# API Contract: Web Search Tool

**Branch**: `002-web-search-tool` | **Date**: 2026-04-07

## Existing Endpoints (Unchanged)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/conversations` | List conversations (paginated) |
| POST | `/api/conversations` | Create new conversation |
| GET | `/api/conversations/{id}` | Get conversation with messages |
| PATCH | `/api/conversations/{id}` | Update conversation title |
| DELETE | `/api/conversations/{id}` | Delete conversation |

## Modified Endpoint

### `POST /api/conversations/{conversation_id}/chat`

**Change**: The SSE event stream is extended with new event types for tool usage transparency and source citations.

**Request** (unchanged):

```json
{
  "message": "What is the current price of Bitcoin?"
}
```

**Response**: `text/event-stream` (SSE)

#### Event Types

##### `text-delta` (existing, unchanged)

Streamed token from the LLM response.

```
data: {"type": "text-delta", "textDelta": "The current"}
```

##### `tool-start` (new)

Emitted when the agent decides to invoke a tool.

```
data: {"type": "tool-start", "toolName": "duckduckgo_search", "toolInput": "Bitcoin price today"}
```

| Field | Type | Description |
|-------|------|-------------|
| type | string | Always `"tool-start"` |
| toolName | string | Name of the tool being called |
| toolInput | string | The search query the agent formulated |

##### `tool-end` (new)

Emitted when the tool execution completes.

```
data: {"type": "tool-end", "toolName": "duckduckgo_search"}
```

| Field | Type | Description |
|-------|------|-------------|
| type | string | Always `"tool-end"` |
| toolName | string | Name of the completed tool |

##### `sources` (new)

Emitted after all tool calls complete, before the final answer streams. Contains the aggregated source URLs for citation rendering.

```
data: {"type": "sources", "sources": [{"title": "CoinDesk", "url": "https://coindesk.com/...", "snippet": "Bitcoin traded at..."}]}
```

| Field | Type | Description |
|-------|------|-------------|
| type | string | Always `"sources"` |
| sources | array | List of source objects |
| sources[].title | string | Page title |
| sources[].url | string | Source URL |
| sources[].snippet | string | Result snippet |

##### `finish` (existing, unchanged)

```
data: {"type": "finish", "finishReason": "stop"}
```

##### `error` (existing, unchanged)

```
data: {"type": "error", "error": "Search service unavailable. Answering from training data."}
```

#### Example Full Stream (search-augmented response)

```
data: {"type": "tool-start", "toolName": "duckduckgo_search", "toolInput": "Bitcoin price today"}
data: {"type": "tool-end", "toolName": "duckduckgo_search"}
data: {"type": "sources", "sources": [{"title": "CoinDesk", "url": "https://...", "snippet": "Bitcoin is trading at $67,000..."}]}
data: {"type": "text-delta", "textDelta": "As of today, "}
data: {"type": "text-delta", "textDelta": "Bitcoin is trading "}
data: {"type": "text-delta", "textDelta": "at approximately $67,000 [1].\n\n"}
data: {"type": "text-delta", "textDelta": "**Sources:**\n[1] https://..."}
data: {"type": "finish", "finishReason": "stop"}
```

#### Example Full Stream (no search needed)

```
data: {"type": "text-delta", "textDelta": "Photosynthesis is "}
data: {"type": "text-delta", "textDelta": "the process by which..."}
data: {"type": "finish", "finishReason": "stop"}
```

## Modified Response Schema

### `GET /api/conversations/{id}` — Response Change

The `MessageResponse` schema is extended to include optional tool invocations:

```json
{
  "id": "uuid",
  "title": "Bitcoin prices",
  "created_at": "2026-04-07T12:00:00Z",
  "updated_at": "2026-04-07T12:01:00Z",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "What is the current price of Bitcoin?",
      "created_at": "2026-04-07T12:00:00Z",
      "tool_invocations": []
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "As of today, Bitcoin is trading at approximately $67,000 [1].\n\n**Sources:**\n[1] https://coindesk.com/...",
      "created_at": "2026-04-07T12:00:05Z",
      "tool_invocations": [
        {
          "id": "uuid",
          "tool_name": "duckduckgo_search",
          "tool_input": "Bitcoin price today",
          "tool_output": [
            { "title": "CoinDesk", "snippet": "Bitcoin is trading at...", "url": "https://coindesk.com/..." }
          ],
          "created_at": "2026-04-07T12:00:02Z"
        }
      ]
    }
  ]
}
```

**Backward compatibility**: The `tool_invocations` field defaults to an empty array `[]` for messages without tool usage. Existing frontend code that does not read this field will be unaffected.
