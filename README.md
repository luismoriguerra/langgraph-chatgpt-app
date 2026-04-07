# ChatGPT App

A full-stack ChatGPT-style application built with FastAPI, LangChain, LangGraph, and Astro.

## Tech Stack

**Backend:** Python 3.11+, FastAPI, LangChain, LangGraph, SQLAlchemy 2.0 (async), Alembic, PostgreSQL

**Frontend:** Astro 5, React 19, Vercel AI SDK, react-markdown, TypeScript (strict)

**Infrastructure:** Docker Compose (PostgreSQL 15)

## Features

- Real-time streaming chat via SSE (Server-Sent Events)
- Conversation management (create, list, rename, delete)
- AI-generated conversation titles
- Markdown rendering with syntax highlighting
- Sidebar with conversation history

## Project Structure

```
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── application/     # Use cases, chat graph
│   │   ├── domain/          # Entities, ports (interfaces)
│   │   ├── infrastructure/  # DB models, repositories, LLM service
│   │   └── presentation/    # Routes, schemas, middleware
│   ├── alembic/             # Database migrations
│   └── tests/               # Unit and integration tests
├── frontend/                # Astro + React application
│   └── src/
│       ├── components/      # React components (App, ChatView, Sidebar, etc.)
│       ├── pages/           # Astro pages
│       └── services/        # API client
├── specs/                   # Feature specs and plans
├── docker-compose.yml       # PostgreSQL service
└── Makefile                 # Development commands
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- An OpenAI API key

## Getting Started

### 1. Clone and setup

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 2. Bootstrap everything

```bash
make setup
```

This will:
- Create a Python virtual environment and install backend dependencies
- Install frontend npm dependencies
- Copy environment files if missing
- Start PostgreSQL via Docker Compose
- Run database migrations

### 3. Start the development servers

```bash
make dev
```

This starts both servers concurrently:
- **Backend:** http://localhost:8000 (FastAPI with auto-reload)
- **Frontend:** http://localhost:4321 (Astro dev server)

## Environment Variables

### Root `.env`

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | **Required.** Your OpenAI API key |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5433/chatgpt_app` | PostgreSQL connection string |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `BACKEND_PORT` | `8000` | Backend server port |
| `FRONTEND_URL` | `http://localhost:4321` | Frontend origin for CORS |
| `POSTGRES_DB` | `chatgpt_app` | Database name (Docker Compose) |
| `POSTGRES_USER` | `postgres` | Database user (Docker Compose) |
| `POSTGRES_PASSWORD` | `postgres` | Database password (Docker Compose) |
| `POSTGRES_PORT` | `5433` | Host port mapped to Postgres |

### Frontend `.env`

| Variable | Default | Description |
|---|---|---|
| `PUBLIC_API_URL` | `http://localhost:8000/api` | Backend API base URL |

## Makefile Commands

| Command | Description |
|---|---|
| `make setup` | Full bootstrap: venv, deps, env files, Docker, migrations |
| `make dev` | Start backend and frontend concurrently |
| `make dev-backend` | Start FastAPI dev server with auto-reload |
| `make dev-frontend` | Start Astro dev server |
| `make test` | Run all tests (backend + frontend) |
| `make test-unit` | Run backend unit tests |
| `make test-int` | Run backend integration tests (requires Docker) |
| `make test-frontend` | Run frontend tests |
| `make test-e2e` | Run Playwright E2E tests |
| `make lint` | Run all linters (ruff + eslint) |
| `make format` | Auto-format all code (ruff + prettier) |
| `make typecheck` | Run type checking (mypy + tsc) |
| `make migrate` | Run Alembic migrations |
| `make migration msg="..."` | Generate a new Alembic migration |
| `make docker-up` | Start Docker Compose services |
| `make docker-down` | Stop Docker Compose services |
| `make clean` | Remove build artifacts and caches |
| `make ci` | Run full CI pipeline locally |

## API Overview

### REST Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/conversations` | List all conversations |
| `POST` | `/api/conversations` | Create a new conversation |
| `GET` | `/api/conversations/{id}` | Get a conversation with messages |
| `PATCH` | `/api/conversations/{id}` | Update conversation title |
| `DELETE` | `/api/conversations/{id}` | Delete a conversation |
| `POST` | `/api/conversations/{id}/chat` | Send a message (returns SSE stream) |

### Chat SSE Events

The chat endpoint returns a stream of JSON events:

```
data: {"type": "text-delta", "content": "Hello"}
data: {"type": "text-delta", "content": " world"}
data: {"type": "finish"}
```
