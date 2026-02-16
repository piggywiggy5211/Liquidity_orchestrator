# Liquidity Orchestrator

An asynchronous service that accepts requests for quotes and order creation/execution (onramp/offramp). It queries multiple liquidity providers (emulators) in parallel and selects the optimal route using the Weighted Sum Model (based on latency, fee rate, and availability). It supports fallback on errors/timeouts, records decisions in the database, and publishes events via an "event log"

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
uv run python -m app.main
```

## API Documentation
Once the application is running, you can access the interactive API documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Logging

All logs are written in JSON format to `stdout`. This facilitates log aggregation and analysis in systems like ELK Stack

### Trace ID
The service uses a cross-cutting `trace_id` for each request. This ID is included in every log message associated with that request, including background tasks (like order execution), allowing you to trace the entire lifecycle of an order across different components

### Log Examples

When an order is created and then executed in the background, the logs will share the same `trace_id`:

```json
{"timestamp": "2026-02-16T18:29:03.631833Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "APP HTTP REQUEST  POST URL: http://0.0.0.0:8000/orders", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab", "request_details": {"method": "POST", "url": "http://0.0.0.0:8000/orders", "headers": {"host": "0.0.0.0:8000", "connection": "keep-alive", "content-length": "131", "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36", "accept": "application/json", "dnt": "1", "content-type": "application/json", "x-api-ts": "999", "origin": "http://0.0.0.0:8000", "referer": "http://0.0.0.0:8000/docs", "accept-encoding": "gzip, deflate", "accept-language": "en-US,en;q=0.9,ru;q=0.8"}, "query_params": {}, "body_raw": "{\n  \"direction\": \"on-ramp\",\n  \"pair\": \"USDT-USD\",\n  \"amount\": 100,\n  \"incoming_account\": \"string\",\n  \"outgoing_account\": \"string\"\n}"}}
{"timestamp": "2026-02-16T18:29:03.641605Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Order created with id: 25", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.642229Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "APP HTTP RESPONSE POST STATUS_CODE: 200 URL: http://0.0.0.0:8000/orders", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab", "response_details": {"status_code": 200, "url": "http://0.0.0.0:8000/orders", "headers": {"content-length": "239", "content-type": "application/json"}, "body_raw": ["{\"id\":25,\"status\":\"NEW\",\"direction\":\"on-ramp\",\"pair\":\"USDT-USD\",\"incoming_amount\":\"100\",\"incoming_account\":\"string\",\"outgoing_amount\":\"98.00\",\"outgoing_account\":\"string\",\"commission_amount\":\"2.00\",\"created_at\":\"2026-02-16T18:29:03.632889\"}"]}}
{"timestamp": "2026-02-16T18:29:03.642466Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Executing order_id 25", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.643567Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "127.0.0.1:60018 - \"POST /orders HTTP/1.1\" 200"}
{"timestamp": "2026-02-16T18:29:03.652382Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Changed order_id 25 status to OrderStatus.PROCESSING", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.652588Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Fetching quotes for order 25", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.661012Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Successfully saved quote id: 58 from ProviderB for order_id 25", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.670046Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Successfully saved quote id: 59 from ProviderA for order_id 25", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.679812Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Successfully saved quote id: 60 from ProviderC for order_id 25", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.680237Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Fetched 3 quotes for order_id 25", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.680325Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Building execution plan for order_id 25", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.683741Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Calculated score for quote_id 58, provider_name ProviderB, final_score 7.3714668358690165( fee_rate 0.009663547198490672, latency 16.156916590254696, timeout 0.0)", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.684007Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Calculated score for quote_id 60, provider_name ProviderC, final_score 6.4( fee_rate 0.012456716876276499, latency 0.0, timeout 0.0)", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.684157Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Calculated score for quote_id 59, provider_name ProviderA, final_score 4.6( fee_rate 0.004917724184122084, latency 40.13362841099539, timeout 30.76923076923077)", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.684359Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Send request for provider ProviderB", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:17.575457Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Order 25 successfully completed via ProviderB", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
```

## Architecture Patterns

### Unit of Work (UOW)
The project implements the **Unit of Work** pattern to manage database transactions and provide a consistent interface for repositories. The `UnitOfWorkSqlAlchemy` class ensures that all repositories (`orders`, `quotes`, `outbox`) share the same database session within a single business transaction.

### Background Task Session Management
For asynchronous background tasks (like order execution), the service must ensure that each task has its own database session, as SQLAlchemy's `AsyncSession` is not thread-safe and should not be shared between concurrent tasks.

This is achieved using `contextvars.ContextVar`:
1. **ContextVar**: The `UnitOfWorkSqlAlchemy` stores the current session in a `contextvars.ContextVar`.
2. **Task Wrapper**: When a background task is initiated (e.g., via FastAPI's `BackgroundTasks`), it is wrapped using `service.task_wrapper`.
3. **Session Lifecycle**: The wrapper creates a new session from the `session_factory`, sets it as the current session in the `ContextVar`, and **automatically closes the session** after the task completes.
4. **Transparent Access**: Repositories retrieve the session from the `ContextVar` via a property in the UOW, allowing the same service logic to work seamlessly in both HTTP request contexts and background task contexts.

Example of initiating a background task:
```python
background_tasks.add_task(service.task_wrapper, service.execute_order, order_id)
```
