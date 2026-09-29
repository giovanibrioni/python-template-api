"""Deterministic architecture checks from AGENTS.md. Stdlib only."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
APP = ROOT / "app"
INFRASTRUCTURE = {"core", "api", "health"}
DOMAIN_FILES = (
    "models.py",
    "schemas.py",
    "repository.py",
    "service.py",
    "router.py",
    "exceptions.py",
)


def main() -> int:
    failures: list[str] = []
    domains = domain_packages()
    if not domains:
        failures.append("no domain packages under app/ besides core, api, and health")

    for domain in domains:
        package = APP / domain
        for name in DOMAIN_FILES:
            if not (package / name).is_file():
                failures.append(f"app/{domain}/{name} missing")
        if f"app.{domain}.router" not in (APP / "api" / "v1" / "router.py").read_text():
            failures.append(f"app/{domain}/router.py is not included from app/api/v1/router.py")
        if f"app.{domain}.models" not in (ROOT / "alembic" / "env.py").read_text():
            failures.append(f"app/{domain}/models.py is not imported from alembic/env.py")
        if not fake_repository_exists(domain):
            failures.append(f"tests/unit/{domain}/ has no Fake*Repository class")
        if not has_tests(ROOT / "tests" / "integration" / domain):
            failures.append(f"tests/integration/{domain}/ has no tests")
        if not has_tests(ROOT / "tests" / "integration" / "api" / f"test_{domain}.py"):
            failures.append(f"tests/integration/api/test_{domain}.py has no tests")
        failures.extend(router_returns_model(package / "router.py"))

    failures.extend(transaction_ownership())
    failures.extend(forbidden_calls())

    if failures:
        for item in failures:
            print(f"FAIL {item}")
        return 1
    print(f"OK architecture ({len(domains)} domain package(s): {', '.join(domains)})")
    return 0


def domain_packages() -> list[str]:
    names: list[str] = []
    for path in sorted(APP.iterdir()):
        if not path.is_dir() or path.name.startswith((".", "_")):
            continue
        if path.name in INFRASTRUCTURE:
            continue
        names.append(path.name)
    return names


def fake_repository_exists(domain: str) -> bool:
    root = ROOT / "tests" / "unit" / domain
    if not root.is_dir():
        return False
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name.startswith("Fake") and "Repository" in node.name:
                return True
    return False


def has_tests(path: Path) -> bool:
    files = [path] if path.is_file() else list(path.rglob("*.py")) if path.is_dir() else []
    for file in files:
        tree = ast.parse(file.read_text(), filename=str(file))
        for node in ast.walk(tree):
            is_test = isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            if is_test and node.name.startswith("test_"):
                return True
    return False


def router_returns_model(path: Path) -> list[str]:
    if not path.is_file():
        return []
    tree = ast.parse(path.read_text(), filename=str(path))
    model_names = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith(".models")
        for alias in node.names
    }
    if not model_names:
        return []
    failures: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        returned = annotation_name(node.returns)
        if returned in model_names:
            failures.append(f"{relative(path)}:{node.lineno} handler returns ORM model {returned}")
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            for keyword in decorator.keywords:
                model = annotation_name(keyword.value)
                if keyword.arg == "response_model" and model in model_names:
                    failures.append(
                        f"{relative(path)}:{node.lineno} response_model is ORM model {model}"
                    )
    return failures


def annotation_name(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def transaction_ownership() -> list[str]:
    failures: list[str] = []
    allowed = APP / "core" / "database.py"
    for path in APP.rglob("*.py"):
        if path == allowed:
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            stripped = line.split("#", 1)[0]
            if ".commit(" in stripped or ".rollback(" in stripped:
                failures.append(f"{relative(path)}:{lineno} commit/rollback outside get_session")
    return failures


def forbidden_calls() -> list[str]:
    failures: list[str] = []
    for path in APP.rglob("*.py"):
        text = path.read_text()
        for lineno, line in enumerate(text.splitlines(), start=1):
            code = line.split("#", 1)[0]
            if code.lstrip().startswith("print("):
                failures.append(f"{relative(path)}:{lineno} print() in application code")
        if "opentelemetry" in text and ("_logs" in text or "LoggerProvider" in text):
            failures.append(f"{relative(path)} OpenTelemetry logs API")
    return failures


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
