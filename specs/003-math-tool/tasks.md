# Tasks: Math Solver AI Tool

**Input**: Design documents from `/specs/003-math-tool/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included per Constitution Principle III (Test-First Development — mandatory for every feature).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Database migration and data layer updates to support the new `tool_result` field

- [x] T001 Add `tool_result: str = ""` field to `ToolInvocation` dataclass in `backend/app/domain/entities.py`
- [x] T002 [P] Add `tool_result` nullable Text column to `ToolInvocationModel` in `backend/app/infrastructure/models.py`
- [x] T003 [P] Add `tool_result` field to `ToolInvocationResponse` schema in `backend/app/presentation/schemas.py`
- [x] T004 Generate Alembic migration for `tool_result` column: run `cd backend && alembic revision --autogenerate -m "add_tool_result_to_tool_invocations"` in `backend/alembic/versions/`
- [x] T005 Apply migration and verify with `make migrate`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Generalize the SSE pipeline to emit `tool-result` events for all tools and persist the raw result

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Emit `tool-result` SSE event in `stream_agent_chat` after `on_tool_end` in `backend/app/infrastructure/llm_service.py` — yield `{"type": "tool-result", "data": {"toolName": ..., "toolInput": ..., "result": raw_output}}` for every tool
- [x] T007 Add `tool-result` serializer to `_SSE_SERIALIZERS` dict in `backend/app/presentation/routes/chat.py`
- [x] T008 Collect `tool-result` event data in `send_message_with_agent` and persist `tool_result` string on `ToolInvocation` in `backend/app/application/use_cases.py`
- [x] T009 Add `tool_result` field to `ToolInvocation` TypeScript interface in `frontend/src/types/index.ts`

**Checkpoint**: Foundation ready — tool-result events flow through SSE and persist for all tools (web_search + future calculate)

---

## Phase 3: User Story 1 — Solve a math expression in chat (Priority: P1) MVP

**Goal**: Users can ask math questions and receive correct computed answers from a `calculate` tool in the ReAct agent

**Independent Test**: Send "What is 125 * 8?" in chat and verify the response contains "1000"

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [P] [US1] Unit test for `safe_eval` function: valid arithmetic, division by zero, unsafe expression rejection in `backend/tests/unit/test_chat_graph.py`
- [x] T011 [P] [US1] Unit test for `build_chat_agent` returning agent with both `web_search` and `calculate` tools in `backend/tests/unit/test_chat_graph.py`
- [x] T011a [P] [US1] Unit test for `send_message_with_agent` collecting `tool-result` event and persisting `tool_result` on `ToolInvocation` in `backend/tests/unit/test_chat_use_case.py`
- [ ] T011b [P] [US1] Integration test for math tool chat flow: POST to `/api/conversations/{id}/chat` with math question, verify SSE stream contains `tool-result` event and tool invocation is persisted in DB in `backend/tests/integration/test_chat.py`

### Implementation for User Story 1

- [x] T012 [US1] Implement `safe_eval(expression: str) -> str` helper in `backend/app/application/chat_graph.py` — use `ast.parse` + restricted `eval` with `math` stdlib, `abs`, `round`, `min`, `max`; catch `ZeroDivisionError`, `ValueError`, `SyntaxError` and return `"Error: ..."` strings
- [x] T013 [US1] Create `calculate` tool via `StructuredTool.from_function` in `backend/app/application/chat_graph.py` — description: "Evaluate a mathematical expression and return the numeric result"; wraps `safe_eval`
- [x] T014 [US1] Register `calculate` tool in `build_chat_agent` tools list alongside `search_tool` in `backend/app/application/chat_graph.py`
- [x] T015 [US1] Verify existing unit tests still pass after tool registration changes: run `make test-unit`

**Checkpoint**: Math tool works end-to-end — user sends math question, agent calls calculate, correct answer appears in text response

---

## Phase 4: User Story 2 — Solve multi-step or complex expressions (Priority: P2)

**Goal**: The calculate tool correctly handles parentheses, exponents, square roots, modulo, and math functions

**Independent Test**: Send "What is sqrt(144) + 3**2?" and verify the response contains "21"

### Tests for User Story 2

- [x] T016 [P] [US2] Unit tests for `safe_eval` with complex expressions: `(50+30)*2-15` → `145`, `2**10` → `1024`, `sqrt(144)` → `12.0`, `15 % 4` → `3`, `abs(-42)` → `42` in `backend/tests/unit/test_chat_graph.py`
- [x] T017 [P] [US2] Unit test for `safe_eval` precision: `0.1 + 0.2` returns a float without unnecessary trailing zeros in `backend/tests/unit/test_chat_graph.py`

### Implementation for User Story 2

- [x] T018 [US2] Ensure `safe_eval` strips trailing zeros from float results (e.g., `12.0` stays `12.0` but `34.500` becomes `34.5`) in `backend/app/application/chat_graph.py`
- [x] T019 [US2] Run US2 tests and verify they pass: `make test-unit`

**Checkpoint**: Calculate tool handles all FR-001 through FR-003, FR-007 operations correctly

---

## Phase 5: User Story 3 — Visible tool usage feedback (Priority: P2)

**Goal**: Users see a tool invocation card in the chat showing tool name, expression, and result (or error state). Cards persist across conversation reloads.

**Independent Test**: Send a math question, verify a tool card appears with input/result. Reload the conversation, verify the card reappears.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T020 [P] [US3] Vitest unit test for `ToolResultCard` component: renders tool name, input, result for calculate tool in `frontend/tests/ToolResultCard.test.tsx`
- [x] T021 [P] [US3] Vitest unit test for `ToolResultCard` error state: renders error indicator when result starts with `"Error:"` in `frontend/tests/ToolResultCard.test.tsx`
- [x] T022 [P] [US3] Vitest test for `ChatView` handling `tool-result` SSE event in `frontend/tests/ChatView.test.tsx`

### Implementation for User Story 3

- [x] T023 [US3] Create `ToolResultCard` component in `frontend/src/components/ToolResultCard.tsx` — accepts `toolName`, `toolInput`, `result`, `status` props; renders calculate tool as expression + result card; renders web_search as source count; renders error state with red indicator when result starts with `"Error:"`
- [x] T024 [US3] Handle `tool-result` SSE event in `ChatView.tsx` streaming loop in `frontend/src/components/ChatView.tsx` — accumulate tool results on the assistant message as `toolCalls` array with `{toolName, toolInput, result, status}` entries
- [x] T025 [US3] Render `ToolResultCard` for each active tool call during streaming in `frontend/src/components/ChatView.tsx` — show between SearchIndicator and message content
- [x] T026 [US3] Render persisted `tool_invocations` via `ToolResultCard` when loading a conversation in `frontend/src/components/ChatView.tsx` — map `tool_invocations` from API response to ToolResultCard props on assistant messages
- [x] T027 [US3] Run frontend tests: `make test-frontend`

**Checkpoint**: Tool cards appear during streaming, show correct result or error state, and persist across page reloads

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation, E2E tests, and cleanup

- [x] T028 [P] Playwright E2E test for math tool happy path: send math question, verify tool card + correct answer in `frontend/e2e/math-tool.spec.ts`
- [x] T029 [P] Playwright E2E test for math tool error: send "What is 5/0?", verify error state tool card in `frontend/e2e/math-tool.spec.ts`
- [x] T030 [P] Playwright E2E test for conversation reload: send math question, reload page, verify tool card reappears in `frontend/e2e/math-tool.spec.ts`
- [ ] T031 Run full test suite: `make ci`
- [ ] T032 Run quickstart.md validation: manually verify all steps in `specs/003-math-tool/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (entity/model changes must exist before pipeline uses them)
- **US1 (Phase 3)**: Depends on Phase 2 (tool-result pipeline must be in place)
- **US2 (Phase 4)**: Depends on Phase 3 (calculate tool must exist to test complex expressions)
- **US3 (Phase 5)**: Depends on Phase 2 (tool-result SSE events must be emitted); can run in parallel with US1/US2 on frontend side
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Backend only. Depends on Foundational phase. No frontend dependency — the LLM text response alone delivers value.
- **US2 (P2)**: Backend only. Depends on US1 (same `safe_eval` function, additional test coverage).
- **US3 (P2)**: Frontend only. Depends on Foundational phase (tool-result SSE events). Can proceed in parallel with US1/US2 once Phase 2 is done.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend changes before frontend changes
- Core implementation before integration

### Parallel Opportunities

- T002, T003 can run in parallel (different files)
- T010, T011, T011a, T011b can run in parallel (different files, different test functions)
- T016, T017 can run in parallel (same file, different test functions)
- T020, T021, T022 can run in parallel (different test files)
- T028, T029, T030 can run in parallel (same E2E file, different specs)
- **US3 frontend work (T020-T027) can proceed in parallel with US1/US2 backend work (T010-T019) after Phase 2 completes**

---

## Parallel Example: After Phase 2 Completes

```text
# Developer A (backend): US1 + US2
Task T010: Unit test for safe_eval (write + verify fails)
Task T011: Unit test for build_chat_agent with calculate tool
Task T011a: Unit test for use case tool-result collection
Task T011b: Integration test for math tool chat flow
Task T012: Implement safe_eval
Task T013: Create calculate StructuredTool
Task T014: Register in build_chat_agent
Task T015: Verify all unit tests pass
Task T016-T019: US2 complex expression tests + precision

# Developer B (frontend): US3
Task T020: Vitest for ToolResultCard
Task T021: Vitest for ToolResultCard error state
Task T022: Vitest for ChatView tool-result handling
Task T023: Create ToolResultCard component
Task T024-T026: ChatView SSE handling + reload rendering
Task T027: Verify frontend tests pass
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T009)
3. Complete Phase 3: User Story 1 (T010-T015)
4. **STOP and VALIDATE**: Send "What is 125 * 8?" — verify text answer is "1000"
5. The math tool works even without the ToolResultCard — the LLM text response contains the correct answer

### Incremental Delivery

1. Setup + Foundational → Pipeline ready
2. US1 → Math tool works, answers appear in text (MVP!)
3. US2 → Complex expressions verified via test coverage
4. US3 → Tool cards provide transparency in UI
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US2 share `safe_eval` — US2 is additional test coverage for the same function
- US3 can be deferred without losing core math functionality (MVP is US1 alone)
- The calculate tool uses no external dependencies (Python `math` stdlib + `ast` only)
- Commit after each task or logical group
