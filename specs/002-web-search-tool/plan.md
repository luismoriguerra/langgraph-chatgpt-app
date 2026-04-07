# Implementation Plan: Web Search Tool for AI Chat

**Branch**: `002-web-search-tool` | **Date**: 2026-04-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-web-search-tool/spec.md`

## Summary

Add a DuckDuckGo web search tool to the AI chat using a LangGraph ReAct agent. The agent autonomously decides when to search the web, streams responses with tool-use indicators via SSE, persists search metadata for source citation survival, and displays inline numbered references with clickable URLs. The existing direct `ChatOpenAI` streaming path is replaced by a LangGraph `create_react_agent` graph with `DuckDuckGoSearchResults` bound as a tool.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript strict (frontend)
**Primary Dependencies**: FastAPI, LangChain, LangGraph, langchain-community, duckduckgo-search, SQLAlchemy 2.0 async, Astro, React
**Storage**: PostgreSQL (existing) + new `tool_invocations` table
**Testing**: pytest + pytest-asyncio (BE), Vitest (FE), Playwright (E2E)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (monorepo: backend/ + frontend/)
**Performance Goals**: Search-augmented responses within 10s for 95th percentile (SC-002)
**Constraints**: Max 3 search calls per turn, no API keys for search, streaming via SSE
**Scale/Scope**: Single-user / small-team; no rate limiting or caching for v1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Clean Architecture | PASS | New code follows 4-layer structure: domain entities (`ToolInvocation`, `SearchResult`), application use case (`stream_agent_chat`), infrastructure (`AgentLLMService`, `ToolInvocationRepository`), presentation (SSE route handler). Dependencies flow inward. |
| II | Dependency Injection | PASS | `AgentLLMService` injected via `Depends()`. Search tool injected into agent builder. `ToolInvocationRepository` injected into use case. No module-level singletons. |
| III | Test-First (NON-NEGOTIABLE) | PASS | Plan includes unit tests for all new backend code (domain entities, agent service, use case, route handler) and frontend code (SSE event parsing, search indicator component). Playwright E2E tests verify the full browser journey. Both required before feature is complete. |
| IV | Separation of Concerns | PASS | All AI/search orchestration in backend. Frontend only renders events. No LLM calls in frontend. SSE contract defined in contracts/api.md. |
| V | Interface-Driven Contracts | PASS | `LLMService` protocol extended with `stream_agent_chat`. New `ToolInvocationRepository` protocol. Pydantic models for all new response fields. LangGraph state uses `TypedDict`. |
| VI | Observability & Traceability | PASS | Structured logging for tool invocations (tool name, input, latency). LangGraph node transitions logged. Request ID propagated through agent execution. |
| VII | Simplicity & YAGNI | PASS | Uses `create_react_agent` (prebuilt) instead of custom graph. Single tool (DuckDuckGo). New dependencies justified: `langchain-community` (tool integration), `duckduckgo-search` (search backend). |

## Project Structure

### Documentation (this feature)

```text
specs/002-web-search-tool/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api.md           # SSE protocol extension
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── domain/
│   │   ├── entities.py          # + ToolInvocation, SearchResult dataclasses
│   │   └── ports.py             # + ToolInvocationRepository, updated LLMService
│   ├── application/
│   │   ├── use_cases.py         # + send_message_with_agent use case
│   │   └── chat_graph.py        # Replace stub → build_chat_agent() using create_react_agent
│   ├── infrastructure/
│   │   ├── models.py            # + ToolInvocationModel SQLAlchemy model
│   │   ├── repositories.py      # + SqlAlchemyToolInvocationRepository
│   │   └── llm_service.py       # + AgentLLMService with stream_agent_chat
│   └── presentation/
│       ├── routes/
│       │   └── chat.py          # Update SSE handler for agent events
│       └── schemas.py           # + ToolInvocationResponse, updated MessageResponse
├── alembic/
│   └── versions/
│       └── xxx_add_tool_invocations.py  # New migration
└── tests/
    ├── unit/
    │   ├── test_entities.py     # + ToolInvocation, SearchResult tests
    │   ├── test_agent_service.py # AgentLLMService unit tests
    │   └── test_chat_use_case.py # send_message_with_agent tests
    └── integration/
        └── test_chat.py         # + agent chat integration tests

frontend/
├── src/
│   ├── components/
│   │   ├── ChatView.tsx         # Handle new SSE event types
│   │   ├── MessageBubble.tsx    # Render source citations
│   │   └── SearchIndicator.tsx  # New: "Searching the web..." component
│   ├── services/
│   │   └── api.ts               # No changes needed
│   └── types/
│       └── index.ts             # + ToolInvocation, Source types
├── tests/
│   ├── SearchIndicator.test.tsx # Unit test
│   └── ChatView.test.tsx        # + test SSE event handling
└── e2e/
    └── web-search.spec.ts       # Playwright E2E tests
```

**Structure Decision**: Web application (Option 2) — existing monorepo with `backend/` and `frontend/` directories. No new top-level directories needed.

## Architecture: Key Changes

### Backend Flow (Agent Path)

```
User message
  → POST /api/conversations/{id}/chat
    → send_message_with_agent() use case
      → persist user message
      → load conversation history
      → build_chat_agent() from chat_graph.py
        → create_react_agent(llm.bind_tools([ddg_search]), [ddg_search])
      → astream_events(version="v2")
        → on_tool_start  → yield SSE: tool-start
        → on_tool_end    → collect sources
        → on_chat_model_stream → yield SSE: text-delta
      → emit SSE: sources (aggregated)
      → persist assistant message + tool invocations
      → emit SSE: finish
```

### Frontend Flow

```
User types message → POST to chat endpoint
  → SSE stream opens
    → "tool-start" event  → show SearchIndicator
    → "tool-end" event    → hide SearchIndicator
    → "sources" event     → store sources for citation rendering
    → "text-delta" events → append to message content
    → "finish" event      → mark complete
  → MessageBubble renders markdown with clickable [1] links
```

### Backward Compatibility

- Non-search conversations produce the same event stream as before (`text-delta` → `finish`)
- The `tool_invocations` field on `MessageResponse` defaults to `[]`
- The frontend SSE parser already has a try/catch that ignores unknown events

## Complexity Tracking

No constitution violations. No complexity justification needed.
