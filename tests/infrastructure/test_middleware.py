import json


def test_request_response_logging(capsys, client, clear_idempotency_set, mock_asyncio_sleep):
    payload = {
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 100.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2",
    }
    response = client.post("/orders", json=payload, headers={"X-Api-Ts": "12345"})

    assert response.status_code == 200

    captured = capsys.readouterr().out
    log_lines = [json.loads(line) for line in captured.splitlines() if line.strip()]

    request_logs = [log for log in log_lines if isinstance(log.get("message"), str) and "POST" in log.get("message")]
    response_logs = [
        log for log in log_lines if isinstance(log.get("message"), str) and "STATUS_CODE: 200" in log.get("message")
    ]

    assert len(request_logs) >= 1
    assert len(response_logs) >= 1

    # Check trace_id is present (from LoggerContextMiddleware)
    assert "trace_id" in request_logs[0]
    assert "span_id" in request_logs[0]


def test_request_response_logging_with_iban(capsys, client, clear_idempotency_set, mock_asyncio_sleep):
    # IBAN in headers or body
    iban = "DE12345678901234567890"
    payload = {
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 100.0,
        "incoming_account": "acct-1",
        "outgoing_account": iban,
    }
    client.post("/orders", json=payload, headers={"X-Api-Ts": "12345"})

    captured = capsys.readouterr().out
    assert "DE12****7890" in captured
    assert iban not in captured
