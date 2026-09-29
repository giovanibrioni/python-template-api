# AGENTS.md

Guidance for working in this repository.

## What this repository is

This is an async FastAPI template organized by domain. The example domain is `items`: create, list, and fetch by id.

This cut does not include authentication, CORS, a queue, or an OpenTelemetry collector. Traces stay in process unless `OTEL_EXPORTER_OTLP_ENDPOINT` is set.

The installable package is `app`. Do not rename it when copying the template. The distribution name is `python-template`.

## Layout and request flow

```text
app/
  main.py                 # app, lifespan, exception handlers
  api/v1/router.py        # mounts domain routers under /api/v1
  core/                   # settings, session, logging, traces, middleware
  health/                 # GET /api/v1/health
  items/                  # example domain
alembic/                  # async migrations
tests/unit/               # fakes, no database
tests/integration/        # Postgres, transaction rollback
```

A request moves in one direction:

1. The router translates HTTP.
2. The service applies the rule and raises a domain error when needed.
3. The repository runs SQL.
4. `get_session` owns the `AsyncSession`.

## New domain checklist

1. Add `models`, `schemas`, `repository` (a `Protocol` plus a SQLAlchemy implementation), `service`, `router`, and `exceptions` under a new package.
2. Include the router from `app/api/v1/router.py`.
3. Import the model module from `alembic/env.py` so autogenerate sees the table.
4. Add a migration.
5. Add a unit test whose fake implements the repository protocol.
6. Add an integration test for the repository and one for the API.

## Transactions

`commit` and `rollback` belong only in `get_session`. Repositories flush when they need generated values. Services do not touch the transaction.

Integration tests bind a session with `join_transaction_mode="create_savepoint"`. The request dependency's `commit` becomes a savepoint, and the test rolls back the outer transaction.

## Schemas and errors

Pydantic schemas are separate from SQLAlchemy models. API handlers return schemas. They do not return the model as the response body.

A domain failure is its own exception subclass of `AppError`. The handler in `app/main.py` chooses the HTTP status. `ItemNotFoundError` becomes `404 {"detail": "Item not found"}`.

## Logging

Use `structlog.get_logger()`. Do not use `print`. Do not log secrets. Do not call the OpenTelemetry logs API. The app only emits traces, and a structlog processor copies `trace_id` and `span_id` onto the event when the current span is recording.

## Tests

- `make test-unit` runs `tests/unit` and does not need Docker.
- `make test` needs `make up`. It migrates `app_test` and runs the full suite.
- A fake lives next to the unit test and implements the repository protocol.
- Integration tests use the `session` fixture in `tests/conftest.py`.

## Make targets

| Target | Purpose |
| --- | --- |
| `make help` | List targets |
| `make install` | `uv sync` |
| `make up` | Start Postgres and create `app_test` if needed |
| `make down` | Stop Postgres |
| `make dev` | API on http://127.0.0.1:8000 |
| `make migrate` | `alembic upgrade head` |
| `make revision msg="..."` | Autogenerate a migration |
| `make test-unit` | Unit tests |
| `make test` | Migrate `app_test` and run Pytest |
| `make lint` | Ruff check, Ruff format check, and ty |
| `make review` | Architecture, orphan, env, and merge-risk checks |

## Adapting this template

When cloning into another project:

- Change `name` and `description` in `pyproject.toml`.
- Change `APP_NAME` and `OTEL_SERVICE_NAME`.
- Change `POSTGRES_DB`, and the database user and password if you want different credentials.
- Change the named volume in `docker-compose.yml`.
- Delete the `items` domain once it is no longer the example.

Do not rename the `app` package.
