# Gemini CLI Configuration

This file contains instructions and standards for working on the **Liquidity Orchestrator** project.

## Tech Stack
- **Backend:** FastAPI (Python 3.14+)
- **Dependency Management:** `uv`
- **Database:** SQLAlchemy 2.0 (Async), Alembic
- **Logging:** Loguru
- **Testing:** Pytest (located in `tests/`)

## Architectural Principles
- **Layered Architecture:** `app/api` -> `app/service` -> `app/database` (repositories/uow).
- **Domain Models:** Clear separation into DTOs (`app/service/dto.py`, `app/domain/models.py`), DB models (`app/database/models/`), and API schemas (`app/api/schemas/`).

## Development Rules
- **Type Hinting:** Mandatory use of modern type annotations (Python 3.14+ PEP 695). Using `TypeVar` and `Generic` is prohibited in favor of the `class MyClass[T]:` syntax.
- **TDD:** Testing via TDD (Test-Driven Development) is a mandatory practice. First write tests, then implement minimum functionality, then verify the test passes, then refactor the test, then refactor the code.
- **Testing:** Any functional change must be accompanied by running all tests at the end of the final changes.
- **Surgical Updates:** Avoid mass refactoring unless required by the task.
- **Validation:** Use Pydantic for input data validation.

## Project Commands
- `uv run pytest` — run all tests.
- `uv run alembic upgrade head` — apply DB migrations.
- `uv run ruff check --fix` — check code with linter.
- `uv run ruff format` — auto-format code.
- `uv run mypy .` — type checking.
