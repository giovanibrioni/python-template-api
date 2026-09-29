# Review checklist

Architecture rules live in `AGENTS.md`. This file is the extra judgment the scripts do not encode.

## Architecture (`architecture_check.py`)

A domain package is any direct child of `app/` other than `core`, `api`, and `health`.

The script fails when a domain is missing `models`, `schemas`, `repository`, `service`, `router`, or `exceptions`; when the router is absent from `app/api/v1/router.py`; when `alembic/env.py` does not import `app.<domain>.models`; when `tests/unit/<domain>/` has no `Fake*Repository`; when repository or API integration tests are missing; when a router annotates an ORM model as the response; when `.commit(` or `.rollback(` appears outside `app/core/database.py`; when `print(` is used; or when the OpenTelemetry logs API appears.

Still judge by hand:

- Request flow stays router → service → repository → `get_session`.
- The repository exposes a `Protocol` plus a SQLAlchemy class. The fake implements that protocol.
- Domain failures subclass `AppError`. HTTP status is chosen in `app/main.py`.
- Services do not open sessions or commit.

## Orphans (`orphan_check.py`)

Fails when an `app` module other than `app.main` is never imported from `app/`, `tests/`, or `alembic/`, including relative imports. Fails when an `AppError` subclass is not named in `app/main.py`.

Bugbot covers unused classes inside modules that are imported.

## Consistency (Bugbot, step 2)

No script covers these. Flag them when the diff introduces them:

- Race: check-then-act (read, then insert or update without a unique constraint or row lock) and lost updates on the same row.
- Dual write: one operation writes to the database and to a second store or external call, with no fallback, outbox, or compensation.
- Retry: a retry around a create or other non-idempotent write that has no idempotency key.

A unique constraint that closes an insert race still belongs in the merge-risk index check.

## Env (`env_example_check.py`)

Every `Settings` field in `app/core/config.py` must have a key in `.env.example`. The default env name is the field name uppercased. A string `alias` or `validation_alias` overrides that name.

## Merge risk (`merge_risk_check.py`)

Scope is the diff from the merge-base with `main` or `master` through the working tree, plus untracked files. With no commits, the scope is untracked files.

| Signal | Script | Reviewer |
| --- | --- | --- |
| `upgrade()` calls `op.drop_*`, `rename_table`, `alter_column`, `batch_alter_table`, or destructive `op.execute` | FAIL | Call out lock risk, data loss, and expand/contract |
| `models.py` changed and no file under `alembic/versions/` changed | FAIL | Model drift |
| `schemas.py`, `router.py`, or `app/main.py` changed | WARN | Removed fields, new required fields, path or status changes, renamed JSON keys |
| `repository.py` or `models.py` changed | WARN | New filters or foreign keys without an index in the migration |
| `app/core/config.py` changed | WARN | New setting missing from deploy env, not only `.env.example` |
| path contains `events/` or ends with `events.py` | WARN | Payload and consumer compatibility |

`downgrade()` may drop objects. Do not treat that as a merge blocker.

Breaking API examples: deleting a response field, changing a path, making an optional request field required, changing a documented status code. Adding an optional response field is compatible.

Index examples: a new `WHERE` column, a new foreign key, or a new `ORDER BY` on a large table without `index=True` or an `op.create_index` in the same change.
