<!--
  Sync Impact Report
  ==================
  Version change: 1.1.0 → 1.2.0
  Modified principles: None (all 7 principles unchanged)
  Added sections:
    - Build Automation row in Technology Stack table
    - "Makefile (Developer Experience)" subsection under
      Development Workflow & Quality Gates
  Removed sections: None
  Modified sections:
    - "Database & Local Development": replaced vague "make target
      or script" sentence with reference to the new Makefile section
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ reviewed (no changes needed)
    - .specify/templates/spec-template.md ✅ reviewed (no changes needed)
    - .specify/templates/tasks-template.md ✅ reviewed (no changes needed)
    - .specify/templates/checklist-template.md ✅ reviewed (no changes needed)
  Follow-up TODOs: None
-->

# LangGraph AI Platform Constitution

## Core Principles

### I. Clean Architecture (Hexagonal / Ports & Adapters)

All code MUST be organized into four explicit layers with
strictly enforced dependency rules:

- **Domain layer**: Pure business logic and entities with zero
  framework imports. This layer MUST NOT depend on any other layer.
- **Application layer**: Use cases and orchestration. Depends only
  on the domain layer. Coordinates LangGraph graph definitions,
  LangChain chain composition, and service workflows.
- **Infrastructure layer**: Concrete implementations of external
  concerns (databases, LLM providers, message brokers, file storage).
  Implements interfaces defined in the domain or application layers.
- **Presentation layer**: FastAPI route handlers (backend) and Astro
  pages/components (frontend). This layer is a thin adapter that
  delegates to the application layer.

Dependencies MUST flow inward: Presentation → Application → Domain.
Infrastructure implements domain/application interfaces but is never
imported directly by application or domain code.

### II. Dependency Injection

All service dependencies MUST be injected, never hard-coded:

- Python services MUST receive collaborators through constructor
  parameters or FastAPI's `Depends()` mechanism.
- LLM clients, vector stores, and external API clients MUST be
  injected as protocol-typed parameters so they can be replaced
  with test doubles.
- Database sessions MUST be injected via FastAPI `Depends()` using
  a session factory. No direct `Session()` instantiation inside
  service or repository code.
- No module-level singleton instantiation of stateful services.
  Factory functions or DI containers MUST be used instead.
- Astro frontend MUST receive backend URLs and configuration
  through environment variables, never hardcoded strings.

### III. Test-First Development (NON-NEGOTIABLE)

Every feature MUST follow the Red-Green-Refactor cycle:

- Tests MUST be written before implementation code.
- Tests MUST fail (Red) before any production code is written.
- Production code MUST be the minimum required to pass (Green).
- Code MUST then be refactored while keeping tests green.
- Unit tests MUST cover domain and application layers in isolation
  using test doubles for all infrastructure dependencies.
- Integration tests MUST verify LangGraph graph execution,
  FastAPI endpoint contracts, and LLM chain behavior using
  recorded/mocked responses.
- Database integration tests MUST run against a real PostgreSQL
  instance (via Docker Compose test profile) with transactional
  rollback to ensure isolation between test cases.
- Frontend component tests MUST verify Astro component rendering
  and user interaction flows.

### IV. Separation of Concerns

Backend and frontend are independent deployable units with a
clearly defined API contract:

- **Backend** (FastAPI + LangChain + LangGraph): Exposes a REST
  and/or WebSocket API. All AI/LLM orchestration lives here.
  No HTML rendering or frontend logic in the backend.
- **Frontend** (Astro): Consumes the backend API. No direct LLM
  calls or business logic in the frontend. UI components MUST be
  purely presentational with data fetching delegated to service
  modules.
- Shared types or schemas MUST be defined in a contracts directory
  and kept in sync between backend and frontend.

### V. Interface-Driven Contracts

Code MUST program against abstractions, not concrete implementations:

- Python code MUST use `typing.Protocol` or `abc.ABC` to define
  service boundaries (LLM providers, storage, retrieval, etc.).
- Repository interfaces MUST abstract all database access. Domain
  and application layers MUST NOT import SQLAlchemy models or
  session objects directly.
- TypeScript code in Astro MUST use interfaces for API response
  types and service contracts.
- LangGraph nodes MUST accept typed state objects and return typed
  state updates; raw dicts are not permitted for graph state.
- All API endpoints MUST have Pydantic models for request/response
  validation. No untyped `dict` returns from FastAPI handlers.

### VI. Observability & Traceability

AI applications require first-class observability:

- All LLM calls MUST be traced with request/response correlation
  IDs using LangChain callbacks or LangSmith integration.
- Structured JSON logging MUST be used throughout the backend.
  No bare `print()` statements in production code.
- FastAPI middleware MUST attach a request ID to every inbound
  request and propagate it through the call chain.
- LangGraph graph executions MUST log state transitions between
  nodes for debugging and auditability.
- Error responses MUST include correlation IDs for support
  traceability without exposing internal details.

### VII. Simplicity & YAGNI

Start with the simplest viable solution:

- No abstraction layer MUST be introduced unless it solves a
  concrete, present problem. Speculative generalization is
  prohibited.
- New dependencies MUST be justified with a documented rationale.
- LangGraph graphs MUST start with the minimal node set; nodes
  MUST be added incrementally as requirements demand.
- Premature optimization is prohibited. Performance work MUST be
  driven by measured bottlenecks, not assumptions.

## Technology Stack & Constraints

| Concern        | Technology                        | Version Policy       |
|----------------|-----------------------------------|----------------------|
| Backend API    | FastAPI                           | Latest stable        |
| AI Framework   | LangChain + LangGraph             | Latest stable        |
| Frontend       | Astro                             | Latest stable        |
| Language (BE)  | Python 3.11+                      | Minimum 3.11         |
| Language (FE)  | TypeScript                        | Strict mode required |
| Database       | PostgreSQL                        | Latest stable (15+)  |
| ORM            | SQLAlchemy 2.0 (async)            | Latest stable        |
| Migrations     | Alembic                           | Latest stable        |
| Local Dev      | Docker Compose                    | Latest stable        |
| Build Automate | GNU Make (Makefile)               | Any                  |
| Testing (BE)   | pytest + pytest-asyncio           | Latest stable        |
| Testing (FE)   | Vitest or Astro test utilities    | Latest stable        |
| Linting (BE)   | Ruff                              | Latest stable        |
| Linting (FE)   | ESLint + Prettier                 | Latest stable        |
| Type Check     | mypy (BE) + TypeScript strict (FE)| Enforced in CI       |

**Constraints**:

- Python MUST use virtual environments (venv or Poetry).
  No global package installations for project dependencies.
- All environment-specific configuration MUST be loaded from
  environment variables or `.env` files. No secrets in source.
- Backend and frontend MUST be independently buildable and
  deployable without requiring the other to be co-located.
- LLM API keys and sensitive credentials MUST never appear in
  code, logs, or version control.

**Database & Local Development**:

- A `docker-compose.yml` at the project root MUST define at
  minimum a PostgreSQL service for local development. Additional
  services (Redis, vector stores) MUST be added to the same
  Compose file as needed.
- The backend MUST connect to PostgreSQL using SQLAlchemy 2.0
  async engine. Connection strings MUST be loaded from environment
  variables (`DATABASE_URL`), never hardcoded.
- All schema changes MUST be managed through Alembic migrations.
  Direct DDL execution against the database is prohibited.
- Every Alembic migration MUST include both `upgrade()` and
  `downgrade()` functions. Migrations without a reversible
  downgrade path MUST document the rationale in the migration
  file docstring.
- Alembic's `env.py` MUST auto-discover SQLAlchemy models from
  the infrastructure layer to enable `--autogenerate` support.
- Developers MUST use the root `Makefile` to bootstrap and
  operate the local environment (see Makefile section below).

## Development Workflow & Quality Gates

### Makefile (Developer Experience)

A `Makefile` MUST exist at the project root and serve as the
single entry point for all common development operations. Every
developer interaction (bootstrapping, running, testing, linting)
MUST be achievable through a `make` target.

**Mandatory targets**:

| Target              | Purpose                                              |
|---------------------|------------------------------------------------------|
| `make setup`        | Full bootstrap: install Python + Node deps, copy `.env.example` to `.env` if missing, `docker compose up -d`, `alembic upgrade head` |
| `make dev`          | Start backend (FastAPI with reload) and frontend (Astro dev server) concurrently |
| `make dev-backend`  | Start only the FastAPI dev server with auto-reload    |
| `make dev-frontend` | Start only the Astro dev server                      |
| `make test`         | Run all tests (unit + integration) for backend and frontend |
| `make test-unit`    | Run backend unit tests only (`pytest tests/unit`)    |
| `make test-int`     | Run backend integration tests only (`pytest tests/integration`) |
| `make test-frontend`| Run frontend tests                                   |
| `make lint`         | Run all linters: `ruff check` (BE) + `eslint` (FE)  |
| `make format`       | Auto-format all code: `ruff format` (BE) + `prettier --write` (FE) |
| `make typecheck`    | Run `mypy --strict` (BE) + `tsc --noEmit` (FE)      |
| `make migrate`      | Run `alembic upgrade head`                           |
| `make migration`    | Generate a new Alembic migration (`alembic revision --autogenerate -m "..."`) |
| `make docker-up`    | Start Docker Compose services in detached mode       |
| `make docker-down`  | Stop and remove Docker Compose services              |
| `make clean`        | Remove build artifacts, caches, `__pycache__`, `.mypy_cache`, `node_modules` |
| `make ci`           | Run the full CI pipeline locally: lint + typecheck + test + coverage |

**Makefile rules**:

- Each target MUST include a brief `## description` comment so
  that `make help` can auto-generate a usage summary.
- The default target (`make` with no arguments) MUST print the
  help summary.
- Targets MUST NOT silently swallow errors. All commands MUST
  propagate exit codes so failures are visible.
- Targets that depend on Docker Compose services MUST verify
  containers are running before proceeding, or start them
  automatically.
- The `make setup` target MUST be idempotent: running it
  multiple times MUST NOT corrupt the local environment.
- New Makefile targets MAY be added as the project evolves, but
  the mandatory targets listed above MUST NOT be removed or
  renamed without a constitution amendment.

### Branch Strategy

- Feature branches MUST follow the naming convention
  `<issue-number>-<short-description>`.
- All changes MUST go through pull request review before merging.

### Quality Gates (CI Pipeline)

Every pull request MUST pass all gates before merge:

1. **Lint**: `ruff check` (backend) and `eslint` (frontend)
   report zero errors.
2. **Type Check**: `mypy --strict` (backend) and `tsc --noEmit`
   (frontend) report zero errors.
3. **Migrations**: `alembic check` MUST confirm no model changes
   are missing a corresponding migration. `alembic upgrade head`
   MUST run without errors against a clean database.
4. **Unit Tests**: `pytest tests/unit` and frontend unit tests
   pass with 100% of tests green.
5. **Integration Tests**: `pytest tests/integration` passes
   (requires PostgreSQL via Docker Compose).
6. **Coverage**: Code coverage MUST NOT decrease. New code MUST
   have >= 80% line coverage.

### Code Review Standards

- Reviewers MUST verify adherence to clean architecture layer
  boundaries (Principle I).
- Reviewers MUST verify new services are injected, not
  instantiated inline (Principle II).
- Reviewers MUST verify tests exist and were written before
  implementation (Principle III).
- Reviewers MUST verify that database schema changes are
  accompanied by an Alembic migration with a valid downgrade.

## Governance

This constitution is the authoritative source for all
architectural and process decisions in this project.

- **Supremacy**: This constitution supersedes all other coding
  guidelines, framework defaults, or team conventions where
  they conflict.
- **Amendments**: Any change to this constitution MUST be
  documented with a rationale, reviewed by the team, and
  accompanied by a migration plan for affected code.
- **Compliance**: All pull requests and code reviews MUST verify
  compliance with these principles. Non-compliance MUST be
  flagged and resolved before merge.
- **Complexity Justification**: Any deviation from Principle VII
  (Simplicity) MUST include a written justification in the PR
  description explaining why the added complexity is necessary.
- **Versioning**: This constitution follows semantic versioning.
  MAJOR for principle removals/redefinitions, MINOR for new
  principles or material expansions, PATCH for clarifications.

**Version**: 1.2.0 | **Ratified**: 2026-04-07 | **Last Amended**: 2026-04-07
