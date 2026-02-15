# Liquidity Orchestrator

Project for liquidity orchestration (Onramp/Offramp).

## Installing Dependencies

The project uses `uv` for dependency management.
```bash
uv sync
```

## Database Management (Alembic)
Migrations are located in the `app/database/alembic` directory.

### Running Migrations
To apply all migrations to the database:
```bash
uv run alembic upgrade head
```

### Creating a New Migration
To automatically generate a migration based on changes in SQLAlchemy models:
```bash
uv run alembic revision --autogenerate -m "your description"
```

## Testing
### Running All Tests
```bash
uv run pytest -vv
```


## Running the Application

```bash
uv run uvicorn main:app --reload
```
