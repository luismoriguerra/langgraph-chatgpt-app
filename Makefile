.DEFAULT_GOAL := help
SHELL := /bin/bash

BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV := $(BACKEND_DIR)/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help setup dev dev-backend dev-frontend test test-unit test-int test-frontend test-e2e lint format typecheck migrate migration docker-up docker-down clean ci

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Full bootstrap: deps, env, docker, migrations
	@echo "==> Creating Python virtual environment..."
	python3 -m venv $(VENV)
	$(PIP) install -e "$(BACKEND_DIR)[dev]"
	@echo "==> Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install
	@echo "==> Setting up environment..."
	@test -f .env || cp .env.example .env
	@test -f $(FRONTEND_DIR)/.env || cp $(FRONTEND_DIR)/.env.example $(FRONTEND_DIR)/.env
	@echo "==> Starting Docker services..."
	$(MAKE) docker-up
	@echo "==> Waiting for PostgreSQL..."
	@sleep 3
	@echo "==> Running migrations..."
	$(MAKE) migrate
	@echo "==> Setup complete!"

dev: ## Start backend and frontend concurrently
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## Start FastAPI dev server with auto-reload
	cd $(BACKEND_DIR) && $(VENV)/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port $${BACKEND_PORT:-8000}

dev-frontend: ## Start Astro dev server
	cd $(FRONTEND_DIR) && npm run dev

test: ## Run all tests (backend + frontend)
	$(MAKE) test-unit
	$(MAKE) test-int
	$(MAKE) test-frontend

test-unit: ## Run backend unit tests only
	cd $(BACKEND_DIR) && $(VENV)/bin/pytest tests/unit -v

test-int: ## Run backend integration tests (requires Docker)
	@docker compose ps --status running | grep -q postgres || $(MAKE) docker-up
	cd $(BACKEND_DIR) && $(VENV)/bin/pytest tests/integration -v

test-frontend: ## Run frontend tests
	cd $(FRONTEND_DIR) && npm run test

test-e2e: ## Run Playwright E2E tests against the full stack
	cd $(FRONTEND_DIR) && npx playwright test

lint: ## Run all linters
	cd $(BACKEND_DIR) && $(VENV)/bin/ruff check .
	cd $(FRONTEND_DIR) && npm run lint

format: ## Auto-format all code
	cd $(BACKEND_DIR) && $(VENV)/bin/ruff format .
	cd $(FRONTEND_DIR) && npm run format

typecheck: ## Run type checking (mypy + tsc)
	cd $(BACKEND_DIR) && $(VENV)/bin/mypy app
	cd $(FRONTEND_DIR) && npm run typecheck

migrate: ## Run alembic upgrade head
	cd $(BACKEND_DIR) && $(VENV)/bin/alembic upgrade head

migration: ## Generate a new Alembic migration (usage: make migration msg="description")
	cd $(BACKEND_DIR) && $(VENV)/bin/alembic revision --autogenerate -m "$(msg)"

docker-up: ## Start Docker Compose services
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@docker compose ps

docker-down: ## Stop and remove Docker Compose services
	docker compose down

clean: ## Remove build artifacts and caches
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(BACKEND_DIR)/.mypy_cache $(BACKEND_DIR)/.ruff_cache $(BACKEND_DIR)/.pytest_cache
	rm -rf $(BACKEND_DIR)/htmlcov $(BACKEND_DIR)/.coverage
	rm -rf $(FRONTEND_DIR)/node_modules $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/.astro
	rm -rf $(VENV)

ci: ## Run full CI pipeline locally
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test-unit
	$(MAKE) test-int
	cd $(BACKEND_DIR) && $(VENV)/bin/pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
	$(MAKE) test-frontend
	@echo "==> CI pipeline passed!"
