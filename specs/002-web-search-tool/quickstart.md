# Quickstart: Web Search Tool Verification

**Branch**: `002-web-search-tool` | **Date**: 2026-04-07

## Prerequisites

1. Docker and Docker Compose installed
2. OpenAI API key set in `.env` (`OPENAI_API_KEY=sk-...`)
3. Python 3.11+ and Node.js 18+ installed

## Setup

```bash
make setup
```

This installs all backend/frontend dependencies, starts PostgreSQL, and runs migrations (including the new `tool_invocations` table).

## Start Dev Servers

```bash
make dev
```

Backend runs at `http://localhost:8000`, frontend at `http://localhost:4321`.

## Verification Steps

### 1. Search-Augmented Response (US1 — P1)

1. Open `http://localhost:4321` in a browser
2. Click "New Chat"
3. Type: **"What is the current price of Bitcoin?"**
4. **Verify**:
   - A "Searching the web..." indicator appears
   - The AI responds with a current price
   - The response includes numbered references (e.g., `[1]`) with clickable URLs

### 2. No-Search Response (US1 — P1, scenario 3)

1. In the same conversation, type: **"What is photosynthesis?"**
2. **Verify**:
   - No search indicator appears
   - The AI answers directly from its knowledge
   - No source URLs in the response

### 3. Search Indicator (US2 — P2)

1. Start a new conversation
2. Type: **"What happened in world news today?"**
3. **Verify**:
   - A visual indicator (e.g., "Searching the web...") appears before the answer
   - The indicator disappears once the answer starts streaming

### 4. Multi-Turn Context (US3 — P3)

1. In a conversation, type: **"Tell me about Tesla"**
2. Wait for the response
3. Then type: **"What is their current stock price?"**
4. **Verify**:
   - The AI searches for "Tesla stock price" (not just "stock price")
   - The response references Tesla specifically

### 5. Persistence (FR-007)

1. After step 1, note the source URLs in the response
2. Refresh the browser page
3. Reopen the same conversation
4. **Verify**:
   - The source URLs are still visible and clickable
   - The full conversation history is preserved

### 6. Search Failure Graceful Degradation (FR-008)

1. Disconnect from the internet (or simulate a network failure)
2. Ask a current-events question
3. **Verify**:
   - The AI responds with a disclaimer that it could not fetch live data
   - It still provides its best answer from training knowledge

### 7. Regression Check (FR-010)

```bash
make test
```

All pre-existing tests must pass.

## Automated Tests

```bash
make test-unit        # Backend + frontend unit tests
make test-e2e         # Playwright E2E tests
```

Both must pass for the feature to be considered complete (Constitution Principle III).
