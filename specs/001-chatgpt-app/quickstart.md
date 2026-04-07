# Quickstart: ChatGPT Application

**Feature**: 001-chatgpt-app
**Date**: 2026-04-07

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Docker and Docker Compose
- GNU Make
- An OpenAI API key (or compatible LLM provider)

## 1. Clone and Setup

```bash
# From the repository root
make setup
```

This runs the full bootstrap:
1. Creates Python virtual environment and installs backend dependencies
2. Installs frontend Node.js dependencies
3. Copies `.env.example` to `.env` (if not present)
4. Starts PostgreSQL via Docker Compose
5. Runs Alembic migrations

## 2. Configure Environment

Edit `.env` at the project root (created by `make setup` from `.env.example`):

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults shown)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/chatgpt_app
LLM_MODEL=gpt-4o-mini
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:4321
```

Edit `frontend/.env` (created from `frontend/.env.example`):

```bash
PUBLIC_API_URL=http://localhost:8000/api
```

## 3. Start Development Servers

```bash
# Start both backend and frontend concurrently
make dev

# Or start them individually:
make dev-backend   # FastAPI on http://localhost:8000
make dev-frontend  # Astro on http://localhost:4321
```

## 4. Open the Application

Navigate to `http://localhost:4321` in your browser.

You should see:
- A sidebar on the left (empty, no conversations yet)
- A "New Chat" button at the top of the sidebar
- A chat input area in the main content area

Type a message and press Enter (or click Send) to start your first conversation.

## 5. Verify Everything Works

1. **Send a message**: Type "Hello, how are you?" and send. Verify streaming response appears.
2. **Check sidebar**: The new conversation should appear in the sidebar with an AI-generated title.
3. **Create another chat**: Click "New Chat", send a different message. Verify it creates a separate conversation.
4. **Switch conversations**: Click between conversations in the sidebar. Verify messages load correctly.
5. **Delete a conversation**: Delete one conversation. Verify it disappears from the sidebar.
6. **Refresh the page**: Verify all conversations persist after reload.

## Common Make Targets

```bash
make help           # Show all available targets
make test           # Run all tests
make test-unit      # Backend unit tests only
make test-int       # Backend integration tests (requires Docker)
make lint           # Lint backend + frontend
make format         # Auto-format all code
make typecheck      # Type checking (mypy + tsc)
make migrate        # Run pending Alembic migrations
make migration      # Generate a new migration
make docker-up      # Start PostgreSQL
make docker-down    # Stop PostgreSQL
make clean          # Remove caches and artifacts
make ci             # Run full CI pipeline locally
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `make setup` fails on Docker | Ensure Docker daemon is running: `docker info` |
| Database connection refused | Run `make docker-up` and wait a few seconds for PostgreSQL to start |
| `OPENAI_API_KEY` errors | Verify `.env` contains a valid API key |
| Frontend can't reach backend | Check `PUBLIC_API_URL` in `frontend/.env` matches the backend port |
| Alembic migration errors | Run `make docker-down && make docker-up && make migrate` for a fresh database |
