"""Merge-risk signals on the diff against the base branch. Stdlib only.

FAIL: destructive work inside upgrade(), or model changes without a migration.
WARN: API, repository, settings, or event files changed. Warnings do not fail the script.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DESTRUCTIVE = {
    "drop_table",
    "drop_column",
    "drop_index",
    "drop_constraint",
    "rename_table",
    "alter_column",
    "batch_alter_table",
    "execute",
}


def main() -> int:
    changed, scope = changed_files()
    print(f"INFO scope: {scope} ({len(changed)} file(s))")
    if not changed:
        print("OK merge-risk (empty diff)")
        return 0

    failures: list[str] = []
    warnings: list[str] = []
    migrations = [
        path for path in changed if path.startswith("alembic/versions/") and path.endswith(".py")
    ]
    models = [path for path in changed if path.startswith("app/") and path.endswith("/models.py")]
    api = [
        path
        for path in changed
        if path.endswith(("/schemas.py", "/router.py")) or path == "app/main.py"
    ]
    repositories = [path for path in changed if path.endswith("/repository.py")]
    settings = [path for path in changed if path == "app/core/config.py"]
    events = [path for path in changed if "/events/" in f"/{path}" or path.endswith("/events.py")]

    for path in migrations:
        failures.extend(destructive_upgrade(ROOT / path))
    if models and not migrations:
        failures.append(
            "model files changed without an alembic/versions migration: " + ", ".join(models)
        )
    if api:
        warnings.append("API surface changed; check backward compatibility: " + ", ".join(api))
    if repositories or models:
        warnings.append(
            "query or model shape changed; confirm indexes for new filters and foreign keys: "
            + ", ".join(repositories + models)
        )
    if settings:
        warnings.append(
            "Settings changed; confirm .env.example and deploy env: " + ", ".join(settings)
        )
    if events:
        warnings.append("event contract changed; check consumers: " + ", ".join(events))
    else:
        print("INFO no domain event contract in this diff")

    for item in failures:
        print(f"FAIL {item}")
    for item in warnings:
        print(f"WARN {item}")
    if failures:
        return 1
    print("OK merge-risk")
    return 0


def changed_files() -> tuple[list[str], str]:
    if not has_head():
        return untracked(), "untracked files (no commits yet)"
    base, label = merge_base()
    if base is None:
        names = git(["diff", "--name-only", "--diff-filter=ACMRD"]) + untracked()
        return sorted(set(names)), "working tree (no main/master base)"
    names = git(["diff", "--name-only", "--diff-filter=ACMRD", base]) + untracked()
    return sorted(set(names)), f"diff against {label} ({base[:12]})"


def has_head() -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def merge_base() -> tuple[str | None, str | None]:
    for branch in ("main", "master"):
        exists = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if exists.returncode != 0:
            continue
        result = subprocess.run(
            ["git", "merge-base", "HEAD", branch],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip(), branch
    return None, None


def untracked() -> list[str]:
    return git(["ls-files", "--others", "--exclude-standard"])


def git(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        return []
    return [line for line in result.stdout.splitlines() if line]


def destructive_upgrade(path: Path) -> list[str]:
    if not path.is_file():
        return []
    tree = ast.parse(path.read_text(), filename=str(path))
    failures: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "upgrade":
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                continue
            if not isinstance(call.func.value, ast.Name) or call.func.value.id != "op":
                continue
            if call.func.attr not in DESTRUCTIVE:
                continue
            if call.func.attr == "execute" and not execute_is_destructive(call):
                continue
            failures.append(
                f"{path.relative_to(ROOT)}:{call.lineno} upgrade() calls op.{call.func.attr}()"
            )
    return failures


def execute_is_destructive(call: ast.Call) -> bool:
    if not call.args or not isinstance(call.args[0], ast.Constant):
        return True
    if not isinstance(call.args[0].value, str):
        return True
    sql = call.args[0].value.upper()
    return any(token in sql for token in ("DROP ", "ALTER ", "RENAME ", "TRUNCATE "))


if __name__ == "__main__":
    sys.exit(main())
