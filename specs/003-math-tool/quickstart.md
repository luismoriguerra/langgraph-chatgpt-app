# Quickstart: Math Solver AI Tool

**Branch**: `003-math-tool` | **Date**: 2026-04-07

## Prerequisites

- Running local environment (`make setup` completed)
- PostgreSQL running (`make docker-up`)
- OpenAI API key configured in `.env`

## Development Workflow

### 1. Apply database migration

```bash
make migrate
```

This runs the new migration adding `tool_result` column to `tool_invocations`.

### 2. Start development servers

```bash
make dev
```

Backend runs on `http://localhost:8000`, frontend on `http://localhost:4321`.

### 3. Test the math tool

Open the chat at `http://localhost:4321` and send:
- "What is 125 * 8?" — should show a calculate tool card with result "1000"
- "What is the square root of 144?" — should show result "12.0"
- "What is 5 / 0?" — should show an error state in the tool card

### 4. Run tests

```bash
make test-unit        # Backend unit tests
make test-frontend    # Frontend Vitest tests
make test-e2e         # Playwright E2E tests
```

## Key Files to Understand

| File | What it does |
|------|-------------|
| `backend/app/application/chat_graph.py` | Defines tools and builds the ReAct agent |
| `backend/app/infrastructure/llm_service.py` | Streams agent events, emits SSE event types |
| `backend/app/application/use_cases.py` | Orchestrates chat flow, persists tool invocations |
| `frontend/src/components/ToolResultCard.tsx` | Renders tool invocation details in chat |
| `frontend/src/components/ChatView.tsx` | Handles SSE streaming and state management |

## Adding Another Tool (Future Reference)

To add a new tool after this feature:

1. Define the tool function in `backend/app/application/chat_graph.py`
2. Register it in `build_chat_agent()` tools list
3. (Optional) Add a tool-specific render branch in `frontend/src/components/ToolResultCard.tsx`

No other changes needed — the SSE pipeline, persistence, and frontend handling are generic.
