# Gemini CLI Configuration

This file contains instructions and standards for working on the **Liquidity Orchestrator workspace** apps.

## Tech Stack
- **Backend:** FastAPI (Python 3.14+)
- **Dependency Management:** `uv`
- **Database:** SQLAlchemy 2.0 (Async), Alembic
- **Logging:** Loguru
- **Testing:** Pytest (located in `app_name/tests/`)

## Architectural Principles
- **Layered Architecture:** `app_name/entrypoints/fastapi` -> `app_name/service` -> `app_name/domain` (logic/models) -> `app_name/database` (infrastructure/repositories).
- **Domain Models:** Clear separation into DTOs (`app_name/service/dto.py`), Domain Models (`app_name/domain/models.py`), DB models (`app_name/database/models/`), and API schemas (`app_name/entrypoints/fastapi/api/schemas/`).

## Development Rules
- **Type Hinting:** Mandatory use of modern type annotations (Python 3.14+ PEP 695). Using `TypeVar` and `Generic` is prohibited in favor of the `class MyClass[T]:` syntax.
- **TDD:** Testing via TDD (Test-Driven Development) is a mandatory practice. First write tests, then implement minimum functionality, then verify the test passes, then refactor the test, then refactor the code.
- **Testing:** Any functional change must be accompanied by running all tests at the end of the final changes.
- **Surgical Updates:** Avoid mass refactoring unless required by the task.
- **Validation:** Use Pydantic for input data validation.

## Project Commands
- `task test:all` — run all tests across the workspace.
- `uv run alembic upgrade head` — apply DB migrations (run from the `liquidity_orchestrator` directory).
- `task ruff` — check and auto-format code with linter.
- `task mypy` — run type checking.
- `task check` — run all checks (tests, linters, type hints).
- `task run:orchestrator` — run main application.
- `task run:mock` — run mock providers' application.
