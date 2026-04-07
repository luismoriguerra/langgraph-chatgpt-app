# API Contracts: ChatGPT Application

**Feature**: 001-chatgpt-app
**Date**: 2026-04-07
**Base URL**: `http://localhost:8000/api`

## Conventions

- All endpoints return JSON unless otherwise noted (streaming endpoints return SSE).
- All timestamps are ISO 8601 with timezone (`YYYY-MM-DDTHH:MM:SS.sssZ`).
- IDs are UUIDs (string format).
- Error responses follow a consistent shape: `{ "detail": "..." }`.
- CORS is enabled for the frontend origin (`http://localhost:4321` in dev).

---

## Endpoints

### 1. List Conversations

```
GET /api/conversations
```

Returns all conversations ordered by most recently active first.

**Query Parameters**:

| Param  | Type | Default | Description            |
|--------|------|---------|------------------------|
| limit  | int  | 50      | Max conversations      |
| offset | int  | 0       | Pagination offset      |

**Response** `200 OK`:

```json
{
  "conversations": [
    {
      "id": "uuid-string",
      "title": "How to deploy FastAPI",
      "created_at": "2026-04-07T10:00:00.000Z",
      "updated_at": "2026-04-07T12:30:00.000Z"
    }
  ],
  "total": 12
}
```

---

### 2. Get Conversation with Messages

```
GET /api/conversations/:id
```

Returns a single conversation with all its messages.

**Path Parameters**: `id` (UUID)

**Response** `200 OK`:

```json
{
  "id": "uuid-string",
  "title": "How to deploy FastAPI",
  "created_at": "2026-04-07T10:00:00.000Z",
  "updated_at": "2026-04-07T12:30:00.000Z",
  "messages": [
    {
      "id": "uuid-string",
      "role": "user",
      "content": "How do I deploy FastAPI to production?",
      "created_at": "2026-04-07T10:00:00.000Z"
    },
    {
      "id": "uuid-string",
      "role": "assistant",
      "content": "There are several options for deploying FastAPI...",
      "created_at": "2026-04-07T10:00:02.000Z"
    }
  ]
}
```

**Response** `404 Not Found`:

```json
{ "detail": "Conversation not found" }
```

---

### 3. Create Conversation

```
POST /api/conversations
```

Creates a new empty conversation. Called when the user sends the first message in a new chat.

**Request Body**:

```json
{
  "title": "New conversation..."
}
```

**Response** `201 Created`:

```json
{
  "id": "uuid-string",
  "title": "New conversation...",
  "created_at": "2026-04-07T10:00:00.000Z",
  "updated_at": "2026-04-07T10:00:00.000Z"
}
```

---

### 4. Delete Conversation

```
DELETE /api/conversations/:id
```

Permanently deletes a conversation and all its messages (cascade).

**Path Parameters**: `id` (UUID)

**Response** `204 No Content` (success, empty body)

**Response** `404 Not Found`:

```json
{ "detail": "Conversation not found" }
```

---

### 5. Send Message (Streaming Chat)

```
POST /api/conversations/:id/chat
```

Sends a user message and streams the AI response via Server-Sent Events. This is the primary chat endpoint. It persists the user message, runs the LangGraph chat graph, streams the response, and persists the assistant message upon completion.

**Path Parameters**: `id` (UUID)

**Request Body**:

```json
{
  "message": "How do I deploy FastAPI to production?"
}
```

**Request Headers**:
- `Content-Type: application/json`

**Response** `200 OK` with `Content-Type: text/event-stream`:

SSE stream following the Vercel AI SDK protocol format:

```
data: {"type":"text-delta","textDelta":"There "}
data: {"type":"text-delta","textDelta":"are "}
data: {"type":"text-delta","textDelta":"several "}
...
data: {"type":"finish","finishReason":"stop"}
```

**Response** `404 Not Found` (conversation does not exist):

```json
{ "detail": "Conversation not found" }
```

**Response** `422 Unprocessable Entity` (empty/whitespace message):

```json
{ "detail": "Message content must not be empty" }
```

**Response** `502 Bad Gateway` (LLM service error):

```json
{ "detail": "AI service temporarily unavailable. Please try again." }
```

**Side Effects**:
- Persists user message (`role: "user"`) before streaming begins.
- Persists assistant message (`role: "assistant"`) after stream completes.
- Updates `conversation.updated_at`.
- If this is the first message in the conversation, triggers async title generation (background task).

---

### 6. Update Conversation Title

```
PATCH /api/conversations/:id
```

Updates the conversation title. Used internally by the title generation background task, but also available for future manual rename.

**Path Parameters**: `id` (UUID)

**Request Body**:

```json
{
  "title": "Deploying FastAPI to production"
}
```

**Response** `200 OK`:

```json
{
  "id": "uuid-string",
  "title": "Deploying FastAPI to production",
  "created_at": "2026-04-07T10:00:00.000Z",
  "updated_at": "2026-04-07T10:00:00.000Z"
}
```

---

## TypeScript Interfaces (Frontend)

```typescript
interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
}

interface SendMessageRequest {
  message: string;
}

interface CreateConversationRequest {
  title?: string;
}

interface UpdateConversationRequest {
  title: string;
}
```

## Pydantic Schemas (Backend)

```python
class ConversationResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

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
    message: str = Field(..., min_length=1)
```
