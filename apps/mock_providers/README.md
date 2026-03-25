# Mock Providers Service

This is a standalone mock service simulating external liquidity providers (Provider A, B, and C).

## Features
- **In-memory Caching**: Uses `TTLCache` to cache quotes.
- **Latency & Timeout Simulation**: Simulates network latency and API timeouts.
- **Error Simulation**: Randomly declines some order executions.

## Running the Service
You can run the service locally using `uv`:
```bash
# Running from the workspace root
uv run --package mock-providers python -m mock_providers.main
```
The service will start on port `8001`.

## Endpoints
- `GET /provider_{a,b,c}/quote`: Get a quote for a specific pair and direction.
- `POST /provider_{a,b,c}/execute`: Execute an order.

For full OpenAPI documentation, navigate to `http://localhost:8001/docs` after starting the service.
