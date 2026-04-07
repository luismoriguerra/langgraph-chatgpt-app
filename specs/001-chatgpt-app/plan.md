# Implementation Plan: ChatGPT Application

**Branch**: `001-chatgpt-app` | **Date**: 2026-04-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-chatgpt-app/spec.md`

## Summary

Build a ChatGPT-style chat application as a monorepo with an Astro frontend and FastAPI backend. The backend uses LangChain + LangGraph for AI orchestration and PostgreSQL for persistence. Users can send messages with streamed AI responses, browse/resume past conversations in a sidebar, create new chats, and delete conversations. AI responses render as formatted markdown with syntax-highlighted code blocks. Conversation titles are AI-generated summaries.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript strict (frontend)
**Primary Dependencies**: FastAPI, LangChain, LangGraph, SQLAlchemy 2.0 async, Alembic (BE); Astro, Vercel AI SDK, React (islands), react-markdown (FE)
**Storage**: PostgreSQL 15+ via Docker Compose, accessed through SQLAlchemy 2.0 async engine
**Testing**: pytest + pytest-asyncio (BE), Vitest (FE)
**Target Platform**: Modern desktop browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (monorepo: backend + frontend)
**Performance Goals**: First token streaming within 3s (SC-001), sidebar load <1s for 50 conversations (SC-004), no UI freeze during 2,000-word streaming (SC-006)
**Constraints**: Single-user (no auth), Docker Compose local only, no context window management
**Scale/Scope**: Single user, ~50 conversations, desktop-only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Clean Architecture | PASS | Backend organized into domain/application/infrastructure/presentation layers. Dependencies flow inward. |
| II. Dependency Injection | PASS | DB sessions via `Depends()`, LLM clients injected as Protocol-typed parameters, no module-level singletons. |
| III. Test-First | PASS | Tests written before implementation per TDD cycle. Unit tests for domain/application, integration tests for endpoints/repositories. |
| IV. Separation of Concerns | PASS | Frontend (Astro) and backend (FastAPI) are independent deployable units with REST API contract. |
| V. Interface-Driven | PASS | `typing.Protocol` for repository and LLM service boundaries. Pydantic models for all API schemas. TypeScript interfaces for frontend types. |
| VI. Observability | PASS | Structured JSON logging, request ID middleware, LangChain callback tracing. |
| VII. Simplicity | PASS | Minimal LangGraph graph (2 nodes: chat + title generation). No premature abstractions. |

**Gate result**: ALL PASS. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-chatgpt-app/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api.md
└── tasks.md
```

### Source Code (repository root)

```text
├── Makefile
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities.py
│   │   │   └── ports.py
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── use_cases.py
│   │   │   └── chat_graph.py
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   ├── repositories.py
│   │   │   └── llm_service.py
│   │   └── presentation/
│   │       ├── __init__.py
│   │       ├── dependencies.py
│   │       ├── middleware.py
│   │       ├── schemas.py
│   │       └── routes/
│   │           ├── __init__.py
│   │           ├── conversations.py
│   │           └── chat.py
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       │   ├── test_entities.py
│       │   ├── test_use_cases.py
│       │   └── test_chat_graph.py
│       └── integration/
│           ├── conftest.py
│           ├── test_conversation_routes.py
│           ├── test_chat_routes.py
│           └── test_repositories.py
│
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── astro.config.mjs
    ├── .env.example
    ├── src/
    │   ├── env.d.ts
    │   ├── layouts/
    │   │   └── ChatLayout.astro
    │   ├── pages/
    │   │   └── index.astro
    │   ├── components/
    │   │   ├── Sidebar.tsx
    │   │   ├── ChatView.tsx
    │   │   ├── MessageBubble.tsx
    │   │   ├── ChatInput.tsx
    │   │   └── ConfirmDialog.tsx
    │   ├── services/
    │   │   └── api.ts
    │   └── types/
    │       └── index.ts
    └── tests/
        └── components/
            ├── Sidebar.test.tsx
            ├── ChatView.test.tsx
            └── MessageBubble.test.tsx

```

**Structure Decision**: Web application monorepo (Option 2). Backend and frontend are sibling directories at root. Backend follows hexagonal architecture with four explicit layers inside `app/`. Frontend uses Astro with React islands for interactive components (sidebar, chat view). Shared types defined via API contracts in `specs/001-chatgpt-app/contracts/api.md` and implemented as Pydantic models (BE) and TypeScript interfaces (FE).

## Complexity Tracking

No constitution violations. No complexity justifications required.
