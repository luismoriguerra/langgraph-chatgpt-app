# Tasks: Web Search Tool for AI Chat

**Input**: Design documents from `/specs/002-web-search-tool/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/api.md

**Tests**: Tests are MANDATORY per Constitution Principle III. Unit tests and Playwright E2E tests MUST be written before implementation code (Red-Green-Refactor).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Add new dependencies and database schema

- [x] T001 Add `langchain-community>=0.3.0` and `duckduckgo-search>=6.0.0` to backend/pyproject.toml dependencies
- [x] T002 [P] Add Playwright to frontend devDependencies and create playwright.config.ts in frontend/
- [x] T003 [P] Create Alembic migration for `tool_invocations` table with both `upgrade()` and `downgrade()` functions in backend/alembic/versions/
- [x] T004 [P] Add `make test-e2e` target to Makefile at project root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain entities, ports, infrastructure models, and schemas that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Phase

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T005 [P] Unit tests for SearchResult and ToolInvocation entity validation in backend/tests/unit/test_entities.py
- [x] T006 [P] Unit tests for ToolInvocationResponse and updated MessageResponse schemas in backend/tests/unit/test_schemas.py

### Implementation for Foundational Phase

- [x] T007 [P] Add `SearchResult` and `ToolInvocation` frozen dataclasses in backend/app/domain/entities.py
- [x] T008 [P] Add `ChatEvent` TypedDict, `ToolInvocationRepository` protocol, and `stream_agent_chat` method to `LLMService` protocol in backend/app/domain/ports.py
- [x] T009 [P] Add `ToolInvocationModel` SQLAlchemy model with FK to messages in backend/app/infrastructure/models.py
- [x] T010 Add `SqlAlchemyToolInvocationRepository` implementing the protocol in backend/app/infrastructure/repositories.py
- [x] T011 [P] Add `ToolInvocationResponse`, `SearchResultResponse` Pydantic models and add `tool_invocations` field to `MessageResponse` in backend/app/presentation/schemas.py
- [x] T012 [P] Add `ToolInvocation` and `Source` TypeScript interfaces and update `Message` interface to include optional `tool_invocations` field in frontend/src/types/index.ts

**Checkpoint**: Foundation ready — domain entities, ports, DB model, schemas, and types in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Ask About Current Events (Priority: P1) 🎯 MVP

**Goal**: The AI can search the web via DuckDuckGo, stream search-augmented answers with inline source citations, and persist tool invocations to the database.

**Independent Test**: Send a current-events question (e.g., "What is the current price of Bitcoin?") and verify the response includes up-to-date info with numbered source links. Send a knowledge question (e.g., "What is photosynthesis?") and verify no search occurs.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T014 [P] [US1] Unit tests for `build_chat_agent()` (tool binding, agent creation) in backend/tests/unit/test_chat_graph.py
- [x] T015 [P] [US1] Unit tests for `AgentLLMService.stream_agent_chat()` (event yielding, max 3 tool calls, error handling) in backend/tests/unit/test_agent_service.py
- [x] T016 [P] [US1] Unit tests for `send_message_with_agent()` use case (persist user msg, stream agent, persist assistant msg + tool invocations) in backend/tests/unit/test_chat_use_case.py
- [x] T017 [P] [US1] Unit tests for updated chat SSE route handler (tool-start, tool-end, sources, text-delta events) in backend/tests/unit/test_chat_route.py

### Implementation for User Story 1

- [x] T018 [US1] Implement `build_chat_agent()` using `create_react_agent` with `DuckDuckGoSearchResults` bound via `bind_tools` in backend/app/application/chat_graph.py
- [x] T019 [US1] Implement `AgentLLMService.stream_agent_chat()` using `astream_events(version="v2")` to yield `ChatEvent` objects in backend/app/infrastructure/llm_service.py
- [x] T020 [US1] Implement `send_message_with_agent()` use case: persist user message, run agent, collect tool invocations, persist assistant message and tool invocations in backend/app/application/use_cases.py
- [x] T021 [US1] Update chat SSE route handler to use `send_message_with_agent()` and emit tool-start, tool-end, sources, text-delta events in backend/app/presentation/routes/chat.py
- [x] T022 [US1] Update conversation detail route to eagerly load and include `tool_invocations` in message responses in backend/app/presentation/routes/conversations.py
- [x] T023 [US1] Update ChatView.tsx SSE parser to handle `tool-start`, `tool-end`, and `sources` event types and store sources in state in frontend/src/components/ChatView.tsx
- [x] T024 [US1] Update MessageBubble.tsx to render markdown with clickable source links (numbered references rendered via react-markdown) in frontend/src/components/MessageBubble.tsx
- [x] T025 [US1] Integration test: agent chat endpoint returns tool-start/tool-end/sources/text-delta events for a search query in backend/tests/integration/test_chat.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The AI can search the web, stream answers with source citations, and persist everything.

---

## Phase 4: User Story 2 — Transparent Tool Usage (Priority: P2)

**Goal**: A visual "Searching the web..." indicator appears in the UI when the agent is performing a web search, and disappears when the answer starts streaming.

**Independent Test**: Ask a current-events question and verify the search indicator appears before the answer, then disappears when text starts streaming.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T026 [P] [US2] Unit test for SearchIndicator component (renders text, animates, accepts visible prop) in frontend/tests/SearchIndicator.test.tsx
- [x] T027 [P] [US2] Unit test for ChatView tool-start/tool-end state transitions (indicator shows/hides correctly) in frontend/tests/ChatView.test.tsx

### Implementation for User Story 2

- [x] T028 [US2] Create SearchIndicator.tsx component with "Searching the web..." text and animation in frontend/src/components/SearchIndicator.tsx
- [x] T029 [US2] Integrate SearchIndicator into ChatView.tsx: show on tool-start, hide on first text-delta after tool-end in frontend/src/components/ChatView.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users see when the AI is searching.

---

## Phase 5: User Story 3 — Multi-Turn Search Context (Priority: P3)

**Goal**: Follow-up questions that require web search correctly use conversation context (e.g., "What is their stock price?" after discussing Tesla), and tool invocations load correctly when revisiting past conversations.

**Independent Test**: In a conversation, ask about a company, then follow up with a pronoun-based question requiring search. Verify the agent disambiguates correctly. Reload the page and verify all messages and source links are preserved.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T030 [P] [US3] Unit test for `send_message_with_agent()` with multi-turn history containing prior tool invocations in backend/tests/unit/test_chat_use_case.py
- [x] T031 [P] [US3] Unit test for conversation reload: tool_invocations load from API and render source links in frontend/tests/ChatView.test.tsx

### Implementation for User Story 3

- [x] T032 [US3] Ensure `send_message_with_agent()` passes full conversation history (including prior tool-augmented turns) to the agent in backend/app/application/use_cases.py
- [x] T033 [US3] Ensure ChatView loads and renders tool_invocations from GET conversation response on page reload in frontend/src/components/ChatView.tsx

**Checkpoint**: All user stories should now be independently functional. Multi-turn context works with search.

---

## Phase 6: E2E Tests & Polish

**Purpose**: Playwright E2E tests (MANDATORY per Constitution Principle III) and cross-cutting improvements

### Playwright E2E Tests (MANDATORY)

- [x] T034 [P] Playwright E2E: user asks current-events question → search indicator appears → answer streams with source citations in frontend/e2e/web-search.spec.ts
- [x] T035 [P] Playwright E2E: user asks knowledge question → no search indicator → direct answer without sources in frontend/e2e/web-search.spec.ts
- [x] T036 Playwright E2E: user reloads page → previous conversation loads with source links intact in frontend/e2e/web-search.spec.ts
- [x] T037 Playwright E2E: multi-turn search with pronoun disambiguation in frontend/e2e/web-search.spec.ts
- [x] T038 Playwright E2E: search service failure → graceful fallback with disclaimer (error/edge-case scenario per Constitution Principle III) in frontend/e2e/web-search.spec.ts

### Cross-Cutting Concerns

- [x] T039 [P] Add structured logging for agent tool invocations (tool name, input, latency, request ID) in backend/app/infrastructure/llm_service.py
- [x] T040 [P] Add graceful error handling for DuckDuckGo search failures (timeout, rate limit) with fallback to LLM-only response in backend/app/infrastructure/llm_service.py
- [x] T041 Run full existing test suite (`make test`) to verify zero regressions (FR-010, SC-004)
- [ ] T042 Run quickstart.md verification steps end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (dependencies installed, migration created) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — delivers MVP
- **User Story 2 (Phase 4)**: Depends on Phase 3 (SSE events must exist for indicator to react to)
- **User Story 3 (Phase 5)**: Depends on Phase 3 (agent path must work before testing multi-turn)
- **E2E & Polish (Phase 6)**: Depends on all user stories being complete

### Within Each User Story

- Tests MUST be written and FAIL before implementation begins
- Domain/application code before infrastructure code
- Backend before frontend (SSE events must exist for UI to consume)
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 1 tasks marked [P] can run in parallel
- All Phase 2 tests (T005-T006) can run in parallel
- All Phase 2 implementation tasks marked [P] can run in parallel (after tests)
- All Phase 3 tests (T014-T017) can run in parallel
- Phase 4 and Phase 5 can run in parallel with each other (both depend on Phase 3, not on each other)
- All E2E tests marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together (write first, ensure they fail):
Task: T014 "Unit tests for build_chat_agent() in backend/tests/unit/test_chat_graph.py"
Task: T015 "Unit tests for AgentLLMService in backend/tests/unit/test_agent_service.py"
Task: T016 "Unit tests for send_message_with_agent() in backend/tests/unit/test_chat_use_case.py"
Task: T017 "Unit tests for chat SSE route in backend/tests/unit/test_chat_route.py"

# Then implement sequentially (each makes more tests green):
Task: T018 "build_chat_agent() in chat_graph.py"
Task: T019 "AgentLLMService.stream_agent_chat() in llm_service.py"
Task: T020 "send_message_with_agent() in use_cases.py"
Task: T021 "Update SSE route handler in chat.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (install deps, migration, Playwright config)
2. Complete Phase 2: Foundational (entities, ports, models, schemas)
3. Complete Phase 3: User Story 1 (agent + search + citations)
4. **STOP and VALIDATE**: Test US1 independently — send a search query and verify
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP with web search
3. Add User Story 2 → Test independently → Adds search indicator
4. Add User Story 3 → Test independently → Multi-turn search context
5. Add E2E Tests + Polish → Full quality gate compliance

### Story Independence

- **User Story 1**: Core search + citations (backend + frontend)
- **User Story 2**: Search indicator (frontend only, depends on US1 SSE events)
- **User Story 3**: Multi-turn context (backend tweak + frontend reload, depends on US1 agent path)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Constitution Principle III: Tests MUST be written FIRST and FAIL before implementation
- Constitution Principle III: Both unit tests AND Playwright E2E tests MANDATORY
- Feature is complete ONLY when `make test-unit`, `make test-frontend`, and `make test-e2e` all pass
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
