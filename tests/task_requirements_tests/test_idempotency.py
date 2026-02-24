import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import IDEMPOTENCY_SET
from app.main import main_app


@pytest.fixture
def client():
    # Clear set before each test to ensure isolation
    IDEMPOTENCY_SET.clear()
    with TestClient(main_app) as c:
        yield c


def test_create_order_without_x_api_ts(client):
    response = client.post(
        "/orders",
        json={
            "direction": "on-ramp",
            "pair": "USDT-USD",
            "amount": 100.0,
            "incoming_account": "acct-1",
            "outgoing_account": "acct-2",
        },
    )
    # Status code 400 as per my update in order.py
    assert response.status_code == 400
    assert "Idempotency check failed" in response.json()["detail"]


def test_create_order_idempotency_success_and_duplicate(client, clean_db):
    payload = {
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 100.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2",
    }
    ts = str(int(time.time()))
    headers = {"X-Api-Ts": ts}

    with patch("asyncio.sleep", AsyncMock()):
        # First request
        response1 = client.post("/orders", json=payload, headers=headers)
        assert response1.status_code == 200

        # Second request with same headers and payload (same hash)
        response2 = client.post("/orders", json=payload, headers=headers)
        assert response2.status_code == 400
        assert "Idempotency check failed" in response2.json()["detail"]


def test_create_order_different_ts_same_body(client, clean_db):
    payload = {
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 100.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2",
    }

    with patch("asyncio.sleep", AsyncMock()):
        # First request
        response1 = client.post("/orders", json=payload, headers={"X-Api-Ts": "1"})
        assert response1.status_code == 200
        # Second request with different TS
        response2 = client.post("/orders", json=payload, headers={"X-Api-Ts": "2"})
        assert response2.status_code == 200


def test_create_order_same_ts_different_body(client, clean_db):
    ts = "12345"
    with patch("asyncio.sleep", AsyncMock()):
        # First request
        response1 = client.post(
            "/orders",
            json={
                "direction": "on-ramp",
                "pair": "USDT-USD",
                "amount": 100.0,
                "incoming_account": "a",
                "outgoing_account": "b",
            },
            headers={"X-Api-Ts": ts},
        )
        assert response1.status_code == 200
        # Second request with different body
        response2 = client.post(
            "/orders",
            json={
                "direction": "on-ramp",
                "pair": "USDT-USD",
                "amount": 200.0,
                "incoming_account": "a",
                "outgoing_account": "b",
            },
            headers={"X-Api-Ts": ts},
        )
        assert response2.status_code == 200
