# Research: ChatGPT Application

**Feature**: 001-chatgpt-app
**Date**: 2026-04-07

## R1: Streaming Protocol (Backend → Frontend)

**Decision**: Server-Sent Events (SSE) via FastAPI `StreamingResponse`

**Rationale**: The Vercel AI SDK's `useChat` hook natively consumes SSE streams using the AI SDK protocol format. FastAPI supports SSE through `StreamingResponse` with `text/event-stream` content type. LangGraph's `astream_events` method produces an async generator that maps cleanly to SSE. SSE is unidirectional (server-to-client), which matches the chat pattern where the client sends a POST and receives a streamed response.

**Alternatives considered**:
- **WebSockets**: Bidirectional, but adds connection management complexity. The AI SDK's `useChat` defaults to SSE. WebSockets would require custom transport configuration on both sides. Not justified by YAGNI (Principle VII).
- **Long polling**: Higher latency, more HTTP overhead. Inferior UX for streaming.

## R2: LangGraph Graph Design

**Decision**: Minimal two-graph architecture — one for chat, one for title generation.

**Chat graph** (2 nodes):
1. `prepare_messages` — Formats the conversation history into LangChain message objects, prepends a system prompt.
2. `generate_response` — Calls the LLM via ChatModel and streams the response. Persistence of the response is handled by the use case layer after graph execution, not inside the graph.

**Title graph** (1 node):
1. `generate_title` — Receives the first user message, calls the LLM with a short prompt requesting a <=60 character title. Returns the title string. Runs asynchronously (fire-and-forget from the user's perspective).

**Rationale**: Principle VII (Simplicity) mandates the minimal node set. A two-node chat graph separates message preparation from generation, enabling unit testing of each independently. Persistence is deliberately excluded from the graph to keep graph nodes pure (Principle I — domain layer has no infrastructure imports). The title graph is a separate concern (Principle IV — Separation).

**Alternatives considered**:
- **Single monolithic function**: No graph at all. Rejected because the constitution mandates LangGraph and the graph structure enables future extensibility (e.g., adding retrieval, moderation nodes) without refactoring.
- **Graph with persistence node**: Would require the graph to access the database, violating clean architecture boundaries. Rejected.

## R3: Astro Island Architecture for Interactive Components

**Decision**: Use React as the island framework within Astro via `@astrojs/react`.

**Rationale**: The Vercel AI SDK (`ai/react`) provides React hooks (`useChat`) purpose-built for streaming chat UIs. These hooks handle SSE connection management, message state, loading states, and error handling out of the box. Astro's islands architecture allows these React components to be hydrated client-side while the page shell (layout, sidebar structure) renders as static HTML for fast initial load.

**Interactive islands** (client-side React):
- `Sidebar.tsx` — Conversation list, new chat button, delete actions
- `ChatView.tsx` — Message list + input, uses `useChat` hook
- `MessageBubble.tsx` — Individual message rendering with markdown
- `ChatInput.tsx` — Text area with Enter-to-send, Shift+Enter for newline
- `ConfirmDialog.tsx` — Delete confirmation modal

**Static Astro** (server-rendered):
- `ChatLayout.astro` — Page shell with sidebar/content grid layout
- `index.astro` — Entry point, renders the layout

**Alternatives considered**:
- **Preact**: Lighter weight, but AI SDK's `useChat` is designed for React. Preact compatibility is possible but untested edge cases with hooks.
- **Solid**: AI SDK has a Solid adapter (`ai/solid`), but the Astro Solid integration is less mature than React.
- **Svelte**: AI SDK has a Svelte adapter, but requires a different mental model and the team's stated stack is React-oriented.

## R4: Markdown Rendering in AI Responses

**Decision**: Use `react-markdown` with `remark-gfm` and `rehype-highlight` (or `react-syntax-highlighter`) for code block syntax highlighting.

**Rationale**: `react-markdown` is the most widely used React markdown renderer, supports custom component overrides (for styling code blocks, links, etc.), and integrates naturally with React islands. `remark-gfm` adds GitHub Flavored Markdown support (tables, strikethrough, task lists). `rehype-highlight` or `react-syntax-highlighter` provides syntax highlighting for fenced code blocks, which is a clarified requirement (FR-013).

**Alternatives considered**:
- **`marked` + `DOMPurify`**: String-based rendering requires `dangerouslySetInnerHTML`. XSS risk unless carefully sanitized. React component approach is safer.
- **`markdown-it`**: Similar string-based approach. Less idiomatic in React.
- **MDX**: Overkill for rendering dynamic chat content. Designed for authoring, not runtime rendering.

## R5: Database Session Management (Async SQLAlchemy)

**Decision**: Async `sessionmaker` with `AsyncSession`, injected via FastAPI `Depends()`. Scoped per-request.

**Pattern**:
```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```

**Rationale**: Constitution Principle II mandates dependency injection for database sessions. Using `async with` ensures sessions are properly closed on request completion, including error cases. Per-request scoping prevents session leakage across concurrent requests.

**Test strategy**: Integration tests use a transactional fixture that wraps each test in a transaction and rolls back after, per Constitution Principle III.

**Alternatives considered**:
- **Synchronous SQLAlchemy**: FastAPI is async-first. Mixing sync DB calls with async handlers causes thread pool exhaustion under load.
- **Raw asyncpg**: Skips ORM benefits (model mapping, migration generation, query building). Violates Principle VII by adding manual SQL management complexity.

## R6: AI SDK Chat Protocol Compatibility

**Decision**: Backend implements the Vercel AI SDK chat protocol format for SSE streaming.

**Protocol format**: The AI SDK `useChat` hook expects SSE events in a specific format. The backend's streaming endpoint will format LangGraph output into AI SDK-compatible SSE events using the `data:` prefix format with text deltas.

**Rationale**: Using the AI SDK's native protocol means the frontend `useChat` hook handles message state, streaming, loading indicators, and error handling automatically. This dramatically reduces custom frontend code and aligns with Principle VII (Simplicity).

**Alternatives considered**:
- **Custom SSE format**: Would require reimplementing message state management, streaming parsing, and error handling in the frontend. Significant extra work with no benefit.

## R7: Conversation Title Generation (Async Fire-and-Forget)

**Decision**: Title generation runs as a background task after the first message response completes.

**Flow**:
1. User sends first message in a new conversation.
2. Backend streams the chat response (primary concern).
3. After the chat response is persisted, the backend fires a background task to generate the title via the title LangGraph graph.
4. The title is saved to the database. The frontend polls or receives the title on the next sidebar refresh.

**Rationale**: Title generation should not block the user's first chat response. Running it as a FastAPI `BackgroundTask` keeps the UX snappy. If title generation fails, the fallback (first ~50 characters of the message) is applied immediately.

**Alternatives considered**:
- **Inline (blocking)**: Would delay the first response. Poor UX.
- **WebSocket push**: Over-engineered for a single update. The sidebar re-fetches on navigation anyway.
