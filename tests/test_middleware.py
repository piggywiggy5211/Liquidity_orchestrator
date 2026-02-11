import json
import pytest
from fastapi.testclient import TestClient
from app.main import main_app

def test_request_response_logging(capsys):
    with TestClient(main_app) as client:
        payload = {"amount": 100.0, "currency": "USD", "destination_address": "0x123"}
        response = client.post("/create_order", json=payload)
        
        assert response.status_code == 200
    
    captured = capsys.readouterr().out
    log_lines = [json.loads(line) for line in captured.splitlines() if line.strip()]
    
    # We expect at least two logs from the middleware: request and response
    # Plus potentially others (from router, etc.)
    
    request_logs = [log for log in log_lines if isinstance(log.get("message"), str) and "POST" in log.get("message")]
    response_logs = [log for log in log_lines if isinstance(log.get("message"), str) and  "STATUS_CODE: 200" in log.get("message")]

    assert len(request_logs) >= 1
    assert len(response_logs) >= 1
    
    # Check trace_id is present (from LoggerContextMiddleware)
    assert "trace_id" in request_logs[0]
    assert "span_id" in request_logs[0]

def test_request_response_logging_with_iban(capsys):
    with TestClient(main_app) as client:
        # IBAN in headers or body
        iban = "DE12345678901234567890"
        payload = {"amount": 100.0, "currency": "USD", "destination_address": iban}
        client.post("/create_order", json=payload)
    
    captured = capsys.readouterr().out
    assert "DE12****7890" in captured
    assert iban not in captured
