# Implementation Plan: Math Solver AI Tool

**Branch**: `003-math-tool` | **Date**: 2026-04-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-math-tool/spec.md`

## Summary

Add a `calculate` math tool to the existing LangGraph ReAct agent so the AI can evaluate arithmetic expressions accurately. The tool infrastructure (agent loop, SSE event pipeline, tool invocation persistence, frontend indicator) already exists for the `web_search` tool. This feature extends that infrastructure to support a second tool and adds a generic tool-result display component to the frontend.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript strict (frontend)
**Primary Dependencies**: FastAPI, LangChain, LangGraph, SQLAlchemy 2.0 async (BE); Astro, React, react-markdown (FE)
**Storage**: PostgreSQL 15+ via SQLAlchemy async + Alembic migrations
**Testing**: pytest + pytest-asyncio (BE unit/integration), Vitest (FE unit), Playwright (E2E)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (monorepo: `backend/` + `frontend/`)
**Performance Goals**: No perceivable delay beyond 1 second for tool execution (SC-002)
**Constraints**: Tool evaluation is server-side only; Python `math` stdlib + `ast.literal_eval` for safe expression parsing
**Scale/Scope**: Single new tool added to existing agent; no new DB tables; one new nullable column on `tool_invocations`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Clean Architecture | PASS | Math tool lives in application layer (`chat_graph.py`). No new layer violations. |
| II. Dependency Injection | PASS | `OpenAILLMService` is already injected. Math tool is a pure function, no DI needed. |
| III. Test-First Development | PASS | Plan includes unit tests for tool function, use case, SSE route; Vitest for frontend component; Playwright E2E. |
| IV. Separation of Concerns | PASS | Tool logic is backend-only. Frontend only renders results via SSE events. |
| V. Interface-Driven Contracts | PASS | `LLMService` protocol already has `stream_agent_chat`. No new interfaces needed. |
| VI. Observability | PASS | Existing `structlog` events in `stream_agent_chat` already log tool start/end for any tool name. |
| VII. Simplicity & YAGNI | PASS | Reuses existing ReAct agent and SSE pipeline. Only adds what's necessary: tool function + result display. |

## Project Structure

### Documentation (this feature)

```text
specs/003-math-tool/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── application/
│   │   ├── chat_graph.py          # MODIFY: add calculate tool, register in build_chat_agent
│   │   └── use_cases.py           # MODIFY: collect tool-result events, persist tool_result
│   ├── domain/
│   │   └── entities.py            # MODIFY: add tool_result field to ToolInvocation
│   ├── infrastructure/
│   │   ├── models.py              # MODIFY: add tool_result column to ToolInvocationModel
│   │   ├── llm_service.py         # MODIFY: emit tool-result SSE event after on_tool_end
│   │   └── repositories.py        # NO CHANGE (generic ORM mapping handles new column)
│   └── presentation/
│       ├── schemas.py             # MODIFY: add tool_result to ToolInvocationResponse
│       └── routes/chat.py         # MODIFY: add tool-result serializer to _SSE_SERIALIZERS
├── alembic/versions/
│   └── <new>_add_tool_result_column.py  # NEW: migration for tool_result column
└── tests/
    ├── unit/
    │   ├── test_chat_graph.py     # MODIFY: add tests for calculate tool
    │   └── test_chat_use_case.py  # MODIFY: add tests for tool-result collection
    └── integration/
        └── test_chat.py           # MODIFY: add math tool integration test

frontend/
├── src/
│   ├── components/
│   │   ├── ToolResultCard.tsx     # NEW: generic tool result display component
│   │   ├── ChatView.tsx           # MODIFY: handle tool-result SSE event, render ToolResultCard, render persisted tool_invocations on reload
│   │   └── MessageBubble.tsx      # NO CHANGE (tool cards render via ToolResultCard in ChatView, not inside MessageBubble)
│   └── types/
│       └── index.ts               # MODIFY: add tool_result field to ToolInvocation
├── tests/
│   ├── ToolResultCard.test.tsx    # NEW: unit tests for ToolResultCard
│   └── ChatView.test.tsx          # MODIFY: add tool-result SSE event test
└── e2e/
    └── math-tool.spec.ts          # NEW: Playwright E2E test
```

**Structure Decision**: Web application (Option 2). All changes fit within existing directory layout. One new React component, one new Alembic migration, one new E2E test file.

## Complexity Tracking

No constitution violations. No complexity justification needed.
