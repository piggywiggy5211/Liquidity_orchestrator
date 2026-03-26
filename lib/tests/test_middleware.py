import json

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from lib.logger.logger import setup_logger
from lib.middleware.logger_context import LoggerContextMiddleware
from lib.middleware.logging_request_response import RequestResponseLoggingMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="Test App")

    app.add_middleware(RequestResponseLoggingMiddleware)
    app.add_middleware(LoggerContextMiddleware)

    @app.post("/ping")
    async def ping(request: Request):
        _ = await request.body()
        return {"response": "pong"}

    return app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    with TestClient(app) as client:
        yield client


def test_request_response_logging(capsys, client):
    response = client.post("/ping", json={"request": "ping"})

    assert response.status_code == 200
    assert response.json() == {"response": "pong"}

    captured = capsys.readouterr().out
    log_lines = [json.loads(line) for line in captured.splitlines() if line.strip()]

    request_logs = [log for log in log_lines if isinstance(log.get("message"), str) and "POST" in log.get("message")]
    response_logs = [
        log for log in log_lines if isinstance(log.get("message"), str) and "STATUS_CODE: 200" in log.get("message")
    ]

    assert len(request_logs) >= 1
    assert len(response_logs) >= 1
    assert "pong" in response_logs[0]["response_details"]["body_raw"]

    # Check trace_id is present (from LoggerContextMiddleware)
    assert "trace_id" in request_logs[0]
    assert "span_id" in request_logs[0]
    assert "trace_id" in request_logs[0]
    assert "span_id" in request_logs[0]


def test_request_response_logging_with_iban(capsys, client):
    # IBAN in headers or body
    iban = "DE12345678901234567890"
    client.post("/ping", json={"iban": iban})

    captured = capsys.readouterr().out
    assert "DE12****7890" in captured
    assert iban not in captured
