"""Unimported app modules and domain errors without an HTTP handler. Stdlib only."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
APP = ROOT / "app"
ENTRYPOINTS = {"app.main"}
SCAN_ROOTS = (APP, ROOT / "tests", ROOT / "alembic")


def main() -> int:
    modules = app_modules()
    imported = imported_modules()
    failures: list[str] = []
    for module, path in sorted(modules.items()):
        if module in ENTRYPOINTS or module in imported:
            continue
        failures.append(f"{relative(path)} module {module} is never imported")

    for path, class_name, lineno in app_error_subclasses():
        if class_name not in (APP / "main.py").read_text():
            failures.append(f"{relative(path)}:{lineno} {class_name} has no handler in app/main.py")

    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1
    print(f"OK orphans ({len(modules)} app modules imported or entrypoints)")
    return 0


def app_modules() -> dict[str, Path]:
    modules: dict[str, Path] = {}
    for path in APP.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        relative_parts = path.relative_to(APP).with_suffix("").parts
        modules["app." + ".".join(relative_parts)] = path
    return modules


def imported_modules() -> set[str]:
    found: set[str] = set()
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(), filename=str(path))
            except SyntaxError as exc:
                print(f"FAIL {relative(path)}:{exc.lineno} syntax error")
                continue
            current = module_name_for(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        found.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    base = resolve_from(current, node.module, node.level)
                    if base is None:
                        continue
                    if node.module is not None:
                        found.add(base)
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        found.add(f"{base}.{alias.name}")
    return found


def module_name_for(path: Path) -> str:
    if not path.is_relative_to(APP):
        return ""
    if path.name == "__init__.py":
        parts = path.parent.relative_to(APP).parts
        return "app." + ".".join(parts) if parts else "app"
    return "app." + ".".join(path.relative_to(APP).with_suffix("").parts)


def resolve_from(current: str, module: str | None, level: int) -> str | None:
    if level == 0:
        return module
    if not current:
        return None
    parts = current.split(".")
    if not is_package(current):
        parts = parts[:-1]
    if level > 1:
        parts = parts[: -(level - 1)]
    if module:
        parts.extend(module.split("."))
    return ".".join(parts) if parts else None


def is_package(module: str) -> bool:
    if module == "app":
        return True
    relative_path = Path(*module.split(".")[1:])
    return (APP / relative_path / "__init__.py").is_file()


def app_error_subclasses() -> list[tuple[Path, str, int]]:
    found: list[tuple[Path, str, int]] = []
    for path in APP.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or node.name == "AppError":
                continue
            if inherits_app_error(node):
                found.append((path, node.name, node.lineno))
    return found


def inherits_app_error(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "AppError":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "AppError":
            return True
    return False


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
