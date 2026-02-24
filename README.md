# Liquidity Orchestrator

An asynchronous service that accepts requests for quotes and order creation/execution (onramp/offramp).
It queries multiple liquidity providers (emulators) in parallel and selects the optimal route using the `Weighted Sum Model` (based on `latency`, `fee rate`, and `availability`).
It supports fallback on errors/timeouts, records decisions in the database, and publishes events via an "event log"

## Architecture Patterns

### Unit of Work (UOW)
The project implements the **Unit of Work** pattern to manage database transactions and provide a consistent interface for repositories.
The `UnitOfWorkSqlAlchemy` class ensures that all repositories (`orders`, `quotes`, `outbox`) share the same database session within a single business transaction.

### Transactional Outbox
The service uses the **Transactional Outbox** pattern to ensure reliable event publishing.
Instead of publishing events directly to an external message broker during a business transaction (which could fail), the service saves the event data into an `outbox` table within the same database transaction as the business logic.

- **Atomicity**: Using the **Unit of Work**, the service updates the order status and inserts an event record into the `outbox` table atomically. If the transaction fails, neither the order status nor the event is saved
- **Guaranteed Delivery**: This approach prevents "dual write" problems where a database update succeeds but the message broker notification fails (or vice versa)

### Background Task Session Management
For asynchronous background tasks (like order execution), the service must ensure that each task has its own database session, as SQLAlchemy's `AsyncSession` is not thread-safe and should not be shared between concurrent tasks.

This is achieved using `contextvars.ContextVar`:
1. **ContextVar**: The `UnitOfWorkSqlAlchemy` stores the current session in a `contextvars.ContextVar`.
2. **Task Wrapper**: When a background task is initiated (e.g., via FastAPI's `BackgroundTasks` or `asyncio.create_task` for parallel execution), it is wrapped using `service.uow.switch_session_context_for_task`.
3. **Session Lifecycle**: The wrapper creates a new session from the `session_factory`, sets it as the current session in the `ContextVar`, and **automatically closes the session** after the task completes.
4. **Transparent Access**: Repositories retrieve the session from the `ContextVar` via a property in the UOW, allowing the same service logic to work seamlessly in both HTTP request contexts and background task contexts.

### Dynamic Provider Discovery
The service automatically discovers and registers liquidity providers using a combination of dynamic module importing and the **Subclass Registry** pattern.

1. **Dynamic Discovery**: The `discover_providers` function (in `app/service/providers/__init__.py`) uses `pkgutil.iter_modules` to scan the package for modules starting with `provider_` and imports them dynamically.
2. **Subclass Registry**: Once modules are imported, `BaseProvider.__subclasses__()` is used to automatically collect all available provider classes. This allows adding new providers simply by creating a new file in the directory, without modifying the core service logic.
3. **Lazy Loading**: The `PROVIDERS_LIST` and `PROVIDERS_MAP` are exposed via module-level `__getattr__` (PEP 562), ensuring discovery only happens when these attributes are first accessed.

### Sliding Window Analytics
To ensure provider scoring is based on recent performance data, the system implements a **Sliding Window** pattern via `ProviderStatsMixin`.

- **Purpose**: Tracks real-time metrics (latency and availability) for each liquidity provider to calculate their score in the Weighted Sum Model.
- **Lazy Cleanup**: Statistics are stored in memory. To keep the data relevant, the `cleanup` method is called every time metrics are accessed (e.g., during the scoring process). The cleanup logic only proceeds if there is actually outdated data, avoiding unnecessary processing.
- **Time Window**: Only records within the last `stats_window_seconds` (configurable in `.env`) are retained.
- **Efficiency**: The cleanup process uses `binary search` to efficiently find and remove expired records from the history, ensuring that the analytical data stays fresh without significant performance overhead.



## Logging

All logs are written in JSON format to `stdout`. This facilitates log aggregation and analysis in systems like ELK Stack


### Trace ID
The service uses a cross-cutting `trace_id` for each request.
This ID is included in every log message associated with that request, including background tasks (like order execution),
allowing you to trace the entire lifecycle of an order across different components

### Log Examples

When an order is created and then executed in the background, the logs will share the same `trace_id`:

```json
{"timestamp": "2026-02-16T18:29:03.631833Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "APP HTTP REQUEST  POST URL: http://0.0.0.0:8000/orders", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab", "request_details": {"method": "POST", "url": "http://0.0.0.0:8000/orders", "headers": {"host": "0.0.0.0:8000", "connection": "keep-alive", "content-length": "131", "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36", "accept": "application/json", "dnt": "1", "content-type": "application/json", "x-api-ts": "999", "origin": "http://0.0.0.0:8000", "referer": "http://0.0.0.0:8000/docs", "accept-encoding": "gzip, deflate", "accept-language": "en-US,en;q=0.9,ru;q=0.8"}, "query_params": {}, "body_raw": "{\n  \"direction\": \"on-ramp\",\n  \"pair\": \"USDT-USD\",\n  \"amount\": 100,\n  \"incoming_account\": \"DE12****7890\",\n  \"outgoing_account\": \"DE12****7892\"\n}"}}
{"timestamp": "2026-02-16T18:29:03.641605Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "Order created with id: 25", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab"}
{"timestamp": "2026-02-16T18:29:03.642229Z", "level": "INFO", "service": "liquidity-orchestrator", "message": "APP HTTP RESPONSE POST STATUS_CODE: 200 URL: http://0.0.0.0:8000/orders", "trace_id": "359826cdc5e5a4eb002456c93e3805cd", "span_id": "46e5c8cf4f158dab", "response_details": {"status_code": 200, "url": "http://0.0.0.0:8000/orders", "headers": {"content-length": "239", "content-type": "application/json"}, "body_raw": ["{\"id\":25,\"status\":\"NEW\",\"direction\":\"on-ramp\",\"pair\":\"USDT-USD\",\"incoming_amount\":\"100\",\"incoming_account\":\"DE12****7890\",\"outgoing_amount\":\"98.00\",\"outgoing_account\":\"DE12****7892\",\"commission_amount\":\"2.00\",\"created_at\":\"2026-02-16T18:29:03.632889\"}"]}}
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

### Log Sanitization

To ensure data privacy and security, all logs pass through a **Log Sanitizer** before being written.
This component automatically detects and masks sensitive information, such as International Bank Account Numbers (IBANs).

- **IBAN Masking**: IBANs are partially hidden, preserving only the first 4 and last 4 characters.
  - *Example*: `DE123456789012345678` → `DE12****5678`

### HTTPX Client Logging

The project includes a `LoggingAsyncClient` (based on `httpx.AsyncClient`) designed for detailed logging of outgoing requests to external providers:

1.  **Request/Response Hooks**: Uses `event_hooks` to automatically log request details (URL, method, headers, body) and response details (status code, body).
2.  **Exception Logging**: The `send` method is customized to intercept and log specific exceptions such as `TimeoutException` and `ConnectError`, providing better visibility into network issues.
3.  **Note on Usage**: Currently, this client is **not yet integrated into the flow** because liquidity providers are implemented as emulators (stubs) within the service. However, the client is fully implemented and ready for use when integrating with real external APIs.


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

### Running Linters auto format 
```bash
uv run ruff check --fix
uv run ruff format
uv run mypy .
```



## Running the Application
```bash
uv run python -m app.main
```

## API Documentation
Once the application is running, you can access the interactive API documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
