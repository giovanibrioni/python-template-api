.DEFAULT_GOAL := help

.PHONY: help install up down dev migrate revision openapi test-unit test lint review

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install dependencies into the local virtualenv
	uv sync

up: ## Start Postgres and ensure the app_test database exists
	docker compose up -d --wait
	docker compose exec -T db psql -U postgres -tc \
	  "SELECT 1 FROM pg_database WHERE datname = 'app_test'" \
	  | grep -q 1 || docker compose exec -T db psql -U postgres -c "CREATE DATABASE app_test"

down: ## Stop Postgres
	docker compose down

openapi: ## Write openapi.yaml from the FastAPI app
	uv run python scripts/openapi.py

dev: ## Run the API with reload on http://0.0.0.0:8000
	uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000

migrate: ## Apply database migrations
	uv run alembic upgrade head

revision: ## Autogenerate a migration; pass msg="describe the change"
	@if [ -z "$(msg)" ]; then echo 'Set msg, for example: make revision msg="add widgets"'; exit 1; fi
	uv run alembic revision --autogenerate -m "$(msg)"

test-unit: ## Run unit tests
	uv run pytest tests/unit

test: ## Migrate app_test and run the full test suite
	DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_test uv run alembic upgrade head
	DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_test uv run pytest

lint: ## Run Ruff and ty
	uv run ruff check
	uv run ruff format --check
	uv run ty check

review: ## Architecture, orphan, env, and merge-risk checks
	@status=0; \
	uv run python .cursor/skills/python-template-review/scripts/architecture_check.py || status=1; \
	uv run python .cursor/skills/python-template-review/scripts/orphan_check.py || status=1; \
	uv run python .cursor/skills/python-template-review/scripts/env_example_check.py || status=1; \
	uv run python .cursor/skills/python-template-review/scripts/merge_risk_check.py || status=1; \
	exit $$status
