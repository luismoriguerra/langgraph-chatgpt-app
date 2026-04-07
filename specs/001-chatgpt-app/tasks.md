# Tasks: ChatGPT Application

**Input**: Design documents from `/specs/001-chatgpt-app/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Included per Constitution Principle III (Test-First, NON-NEGOTIABLE). Tests MUST be written and fail before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/app/` for source, `backend/tests/` for tests
- **Frontend**: `frontend/src/` for source, `frontend/tests/` for tests
- **Root**: `Makefile`, `docker-compose.yml`, `.env.example`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency management, and dev tooling

- [ ] T001 Create monorepo directory structure per plan.md (all directories under `backend/app/`, `backend/tests/`, `frontend/src/`, `frontend/tests/`)
- [ ] T002 [P] Create `docker-compose.yml` at project root with PostgreSQL 15 service (port 5432, volume for data persistence, `chatgpt_app` database)
- [ ] T003 [P] Create `.env.example` at project root with all required env vars (`OPENAI_API_KEY`, `DATABASE_URL`, `LLM_MODEL`, `BACKEND_PORT`, `FRONTEND_URL`) and `.gitignore`
- [ ] T004 [P] Initialize backend Python project: `backend/pyproject.toml` with FastAPI, LangChain, LangGraph, SQLAlchemy[asyncio], asyncpg, Alembic, pydantic-settings, uvicorn, pytest, pytest-asyncio, ruff, mypy dependencies
- [ ] T005 [P] Initialize frontend Astro project: `frontend/package.json` with Astro, `@astrojs/react`, React, AI SDK (`ai`, `@ai-sdk/react`), `react-markdown`, `remark-gfm`, `react-syntax-highlighter`, Vitest, ESLint, Prettier; configure `frontend/astro.config.mjs` with React integration and `frontend/tsconfig.json` in strict mode
- [ ] T006 Create `Makefile` at project root with all 16 mandatory targets per constitution (setup, dev, dev-backend, dev-frontend, test, test-unit, test-int, test-frontend, lint, format, typecheck, migrate, migration, docker-up, docker-down, clean, ci) plus `help` as default target with `## description` comments

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain, database, and app skeleton that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [P] Create domain entities (`Conversation`, `Message` frozen dataclasses) in `backend/app/domain/entities.py` per data-model.md
- [ ] T008 [P] Create repository protocols (`ConversationRepository`, `MessageRepository`) and LLM service protocol (`LLMService`) in `backend/app/domain/ports.py` using `typing.Protocol`
- [ ] T009 [P] Create backend config with pydantic-settings (`Settings` class loading from env vars: `DATABASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL`, `BACKEND_PORT`, `FRONTEND_URL`) in `backend/app/config.py`
- [ ] T010 Create SQLAlchemy 2.0 async engine, `async_session_factory`, and `get_db_session` generator in `backend/app/infrastructure/database.py`
- [ ] T011 [P] Create SQLAlchemy ORM models (`ConversationModel`, `MessageModel`) with UUID PKs, indexes, and cascade delete in `backend/app/infrastructure/models.py` per data-model.md
- [ ] T012 Configure Alembic: create `backend/alembic.ini` and `backend/alembic/env.py` with async support and model auto-discovery; generate initial migration for Conversation and Message tables in `backend/alembic/versions/`
- [ ] T013 Implement `SqlAlchemyConversationRepository` and `SqlAlchemyMessageRepository` in `backend/app/infrastructure/repositories.py` (all methods from Protocol)
- [ ] T014 [P] Create all Pydantic request/response schemas in `backend/app/presentation/schemas.py` per contracts/api.md (`ConversationResponse`, `MessageResponse`, `ConversationDetailResponse`, `ConversationListResponse`, `CreateConversationRequest`, `UpdateConversationRequest`, `SendMessageRequest`)
- [ ] T015 Create FastAPI app factory in `backend/app/main.py` with CORS middleware (allow frontend origin) and request-ID middleware in `backend/app/presentation/middleware.py`; configure structured JSON logging
- [ ] T016 Create FastAPI dependency injection factories in `backend/app/presentation/dependencies.py`: `get_db_session`, `get_conversation_repo`, `get_message_repo`, `get_llm_service`, `get_settings`
- [ ] T017 [P] Create shared test fixtures in `backend/tests/conftest.py` (mock LLM service, domain entity factories) and `backend/tests/integration/conftest.py` (async test DB session with transactional rollback, test app client)
- [ ] T018 [P] Create frontend TypeScript interfaces in `frontend/src/types/index.ts` per contracts/api.md (`Conversation`, `Message`, `ConversationWithMessages`, `ConversationListResponse`, `SendMessageRequest`)
- [ ] T019 [P] Create frontend API service client in `frontend/src/services/api.ts` with functions for all 6 API endpoints (listConversations, getConversation, createConversation, deleteConversation, updateTitle) using fetch; backend URL from `PUBLIC_API_URL` env var

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Send a Message and Get an AI Response (Priority: P1) MVP

**Goal**: User opens the app, types a message, and receives a streamed AI response with markdown rendering

**Independent Test**: Open app → type message → verify streamed AI response appears with formatted markdown

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T020 [P] [US1] Write unit tests for domain entities (Conversation, Message creation and validation) in `backend/tests/unit/test_entities.py`
- [ ] T021 [P] [US1] Write unit tests for chat graph (prepare_messages formats history, generate_response calls LLM) in `backend/tests/unit/test_chat_graph.py` using mock LLM
- [ ] T022 [P] [US1] Write unit tests for send-message use case (persists user message, invokes graph, persists assistant message, updates timestamp) in `backend/tests/unit/test_use_cases.py` using mock repos and mock LLM
- [ ] T023 [P] [US1] Write integration tests for chat streaming endpoint (`POST /api/conversations/:id/chat`) and create-conversation endpoint (`POST /api/conversations`) in `backend/tests/integration/test_chat_routes.py`
- [ ] T024 [P] [US1] Write integration tests for conversation and message repositories (CRUD operations, cascade delete) in `backend/tests/integration/test_repositories.py`

### Implementation for User Story 1

- [ ] T025 [US1] Implement LLM service (LangChain ChatModel wrapper with streaming support) in `backend/app/infrastructure/llm_service.py`
- [ ] T026 [US1] Implement chat LangGraph graph (prepare_messages + generate_response nodes) in `backend/app/application/chat_graph.py` per research.md R2
- [ ] T027 [US1] Implement title LangGraph graph (generate_title node, <=60 char summary) in `backend/app/application/chat_graph.py`
- [ ] T028 [US1] Implement use cases (CreateConversationUseCase, SendMessageUseCase with streaming, GenerateTitleUseCase as background task with truncation fallback) in `backend/app/application/use_cases.py`
- [ ] T029 [US1] Implement create-conversation route (`POST /api/conversations`) in `backend/app/presentation/routes/conversations.py`
- [ ] T030 [US1] Implement streaming chat route (`POST /api/conversations/:id/chat`) with SSE in AI SDK protocol format in `backend/app/presentation/routes/chat.py` per research.md R1/R6
- [ ] T031 [US1] Register conversation and chat routers in `backend/app/main.py`
- [ ] T032 [P] [US1] Create ChatInput component (textarea with Enter-to-send, Shift+Enter for newline, Send button, empty-message prevention) in `frontend/src/components/ChatInput.tsx`
- [ ] T033 [P] [US1] Create MessageBubble component with react-markdown, remark-gfm, and react-syntax-highlighter for AI responses; plain text for user messages in `frontend/src/components/MessageBubble.tsx`
- [ ] T034 [US1] Create ChatView component using AI SDK `useChat` hook for streaming, message list rendering with MessageBubble, loading indicator, error display with retry in `frontend/src/components/ChatView.tsx`
- [ ] T035 [US1] Create ChatLayout with sidebar placeholder and content area grid in `frontend/src/layouts/ChatLayout.astro`
- [ ] T036 [US1] Create index page rendering ChatLayout with ChatView as React island (`client:load`) in `frontend/src/pages/index.astro`

**Checkpoint**: At this point, User Story 1 should be fully functional — user can send messages and receive streamed, markdown-rendered AI responses. Sidebar is a placeholder. This is the MVP.

---

## Phase 4: User Story 2 — Browse and Resume Past Conversations (Priority: P2)

**Goal**: Sidebar lists past conversations ordered by most recent. User can click to load, continue chatting, or delete conversations.

**Independent Test**: Create several conversations → refresh → verify sidebar lists them → click one → verify messages load → delete one → verify removed

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T037 [P] [US2] Write integration tests for list-conversations endpoint (`GET /api/conversations`), get-conversation endpoint (`GET /api/conversations/:id`), delete-conversation endpoint (`DELETE /api/conversations/:id`), and update-title endpoint (`PATCH /api/conversations/:id`) in `backend/tests/integration/test_conversation_routes.py`

### Implementation for User Story 2

- [ ] T038 [US2] Implement list-conversations route (`GET /api/conversations` with limit/offset, ordered by updated_at DESC) in `backend/app/presentation/routes/conversations.py`
- [ ] T039 [US2] Implement get-conversation-with-messages route (`GET /api/conversations/:id`) in `backend/app/presentation/routes/conversations.py`
- [ ] T040 [US2] Implement delete-conversation route (`DELETE /api/conversations/:id`, cascade) in `backend/app/presentation/routes/conversations.py`
- [ ] T041 [US2] Implement update-title route (`PATCH /api/conversations/:id`) in `backend/app/presentation/routes/conversations.py`
- [ ] T042 [P] [US2] Create ConfirmDialog component (modal with confirm/cancel buttons) in `frontend/src/components/ConfirmDialog.tsx`
- [ ] T043 [US2] Create Sidebar component (conversation list from API, click to select, delete button per entry with ConfirmDialog, scroll for 20+ items, active conversation highlight) in `frontend/src/components/Sidebar.tsx`
- [ ] T044 [US2] Integrate Sidebar into ChatLayout as React island (`client:load`); wire conversation selection to ChatView (load messages via API, continue chatting); wire delete to clear active view if deleted conversation was active in `frontend/src/layouts/ChatLayout.astro` and `frontend/src/pages/index.astro`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — user can chat, browse history, resume past conversations, and delete conversations

---

## Phase 5: User Story 3 — Start a New Conversation (Priority: P3)

**Goal**: "New Chat" button in sidebar clears the content area and begins a fresh conversation. Empty chats are discarded.

**Independent Test**: Click "New Chat" → verify empty view → send message → verify new conversation in sidebar → click "New Chat" without sending → switch to another conversation → verify empty chat was discarded

### Implementation for User Story 3

- [ ] T045 [US3] Add "New Chat" button to Sidebar component (always visible at top, not scrolled away) in `frontend/src/components/Sidebar.tsx`
- [ ] T046 [US3] Implement new-chat state management in ChatView: clear messages, reset useChat hook, track "unsaved new chat" state; on first message send, create conversation via API then send message in `frontend/src/components/ChatView.tsx`
- [ ] T047 [US3] Implement empty-chat discard logic: when user switches to another conversation while in an unsaved new-chat state, discard without persisting in `frontend/src/components/Sidebar.tsx` and `frontend/src/components/ChatView.tsx`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Add structured JSON logging throughout backend (replace any remaining print statements) in `backend/app/`
- [ ] T049 [P] Add LangChain callback tracing for all LLM calls (request/response correlation IDs) in `backend/app/infrastructure/llm_service.py`
- [ ] T050 [P] Write frontend component tests for Sidebar, ChatView, and MessageBubble in `frontend/tests/components/Sidebar.test.tsx`, `frontend/tests/components/ChatView.test.tsx`, `frontend/tests/components/MessageBubble.test.tsx`
- [ ] T051 [P] Add edge case handling: long message validation, rapid-send queuing, partial response on network drop in `backend/app/presentation/routes/chat.py` and `frontend/src/components/ChatView.tsx`
- [ ] T052 Run `make ci` to verify full pipeline (lint + typecheck + all tests + coverage >= 80%) and fix any issues
- [ ] T053 Run quickstart.md validation: follow all steps on a clean environment and verify all 6 verification checks pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — May use US1 components but is independently testable
- **User Story 3 (Phase 5)**: Depends on US2 (needs Sidebar component) — Extends existing Sidebar and ChatView
- **Polish (Phase 6)**: Depends on all user stories being complete

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Domain/application layer before infrastructure
- Infrastructure before presentation
- Backend endpoints before frontend components that consume them
- Core components before integration/wiring

### Parallel Opportunities

**Phase 1** (all [P] tasks):
- T002, T003, T004, T005 can run in parallel after T001

**Phase 2** (all [P] tasks):
- T007, T008, T009, T011, T014 can run in parallel
- T017, T018, T019 can run in parallel (test fixtures + frontend types)

**Phase 3 - US1**:
- T020, T021, T022, T023, T024 (all test tasks) can run in parallel
- T032, T033 (ChatInput, MessageBubble) can run in parallel

**Phase 4 - US2**:
- T042 (ConfirmDialog) can run in parallel with backend route tasks

**Phase 6**:
- T048, T049, T050, T051 can all run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Send a message, verify streaming markdown response
5. Deploy/demo if ready — this is a working ChatGPT app (single conversation)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP: single-conversation chat)
3. Add User Story 2 → Test independently → Demo (multi-conversation with sidebar + delete)
4. Add User Story 3 → Test independently → Demo (new chat button, full feature set)
5. Polish → Run CI → Validate quickstart

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (Red-Green-Refactor per Constitution Principle III)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
