"""Settings fields must appear in .env.example. Stdlib only."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / "app" / "core" / "config.py"
EXAMPLE = ROOT / ".env.example"


def main() -> int:
    if not CONFIG.is_file():
        print("FAIL app/core/config.py missing")
        return 1
    if not EXAMPLE.is_file():
        print("FAIL .env.example missing")
        return 1

    expected = settings_env_names()
    present = example_keys()
    missing = sorted(expected - present)
    if missing:
        for name in missing:
            print(f"FAIL .env.example missing {name}")
        return 1
    print(f"OK env ({len(expected)} settings documented in .env.example)")
    return 0


def settings_env_names() -> set[str]:
    tree = ast.parse(CONFIG.read_text(), filename=str(CONFIG))
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "Settings":
            continue
        for statement in node.body:
            target = statement.target if isinstance(statement, ast.AnnAssign) else None
            if not isinstance(target, ast.Name):
                continue
            if statement.target.id == "model_config":
                continue
            names.add(env_name(statement.target.id, statement.value))
    return names


def env_name(field_name: str, value: ast.expr | None) -> str:
    if isinstance(value, ast.Call):
        for keyword in value.keywords:
            alias = keyword.value
            named = keyword.arg in {"alias", "validation_alias"}
            if named and isinstance(alias, ast.Constant) and isinstance(alias.value, str):
                return alias.value
    return field_name.upper()


def example_keys() -> set[str]:
    keys: set[str] = set()
    for line in EXAMPLE.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        keys.add(stripped.split("=", 1)[0].strip())
    return keys


if __name__ == "__main__":
    sys.exit(main())
