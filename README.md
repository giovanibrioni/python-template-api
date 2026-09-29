# python-template

Async FastAPI backend template. The API runs on the host with `uv`. Postgres runs in Docker.

## Prerequisites

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- Docker, for Postgres

## Setup

```bash
make install
make up
make migrate
make dev
```

Interactive docs: http://127.0.0.1:8000/docs

## Checks

```bash
make test
make lint
make review
uv run pre-commit install
```

`make test-unit` does not need Docker. `make test` uses the `app_test` database started by `make up`.

## Adapting the template

See the checklist in [AGENTS.md](AGENTS.md). Keep the import package named `app`.
