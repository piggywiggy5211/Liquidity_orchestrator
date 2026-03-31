import time
from datetime import datetime, timezone

import httpx
import respx


# Base URL for all providers from settings (default "http://0.0.0.0:8001")
MOCK_PROVIDER_URL = "http://0.0.0.0:8001"


def setup_respx_quotes(respx_mock, amount_in="100.0", amount_out="100.0"):
    provider_names = ["provider_a", "provider_b", "provider_c"]
    for provider in provider_names:
        # Quote route
        respx_mock.get(f"{MOCK_PROVIDER_URL}/{provider}/quote").mock(
            return_value=httpx.Response(
                200,
                json={
                    "direction": "on-ramp",
                    "pair": "USDT-USD",
                    "amount_in": amount_in,
                    "amount_out": amount_out,
                    "fee_rate": "0.02",
                    "valid_until": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                },
            )
        )


def setup_respx_executes(respx_mock, status="success", provider_ref="ref-123"):
    provider_names = ["provider_a", "provider_b", "provider_c"]
    for provider in provider_names:
        # Execute route
        respx_mock.post(f"{MOCK_PROVIDER_URL}/{provider}/execute").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": status,
                    "provider_ref": f"{provider_ref}-{provider}",
                },
            )
        )


@respx.mock
def test_create_order_success_flow(client, clear_idempotency_set, mock_asyncio_sleep):
    payload = {
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 100.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2",
    }
    headers = {"X-Api-Ts": "12345"}

    setup_respx_quotes(respx.mock)
    setup_respx_executes(respx.mock, status="success")

    # 1. Create order
    create_resp = client.post("/orders", json=payload, headers=headers)
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert "id" in data
    assert data["status"] == "NEW"
    order_id = data["id"]

    # 2. Get order to verify it reached COMPLETED
    get_resp = client.get(f"/orders/{order_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == order_id
    assert get_data["status"] == "COMPLETED"


@respx.mock
def test_create_order_failure_flow(client, clear_idempotency_set, mock_asyncio_sleep):
    payload = {
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 100.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2",
    }
    headers = {"X-Api-Ts": "12346"}

    setup_respx_quotes(respx.mock)
    setup_respx_executes(respx.mock, status="decline")

    # 1. Create order
    create_resp = client.post("/orders", json=payload, headers=headers)
    assert create_resp.status_code == 200
    data = create_resp.json()
    assert "id" in data
    assert data["status"] == "NEW"
    order_id = data["id"]

    # 2. Get order to verify it reached FAILED
    get_resp = client.get(f"/orders/{order_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == order_id
    assert get_data["status"] == "FAILED"


def test_get_order_not_found(client):
    response = client.get("/orders/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_create_order_without_x_api_ts(client, clear_idempotency_set):
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
    assert response.status_code == 400
    assert "Idempotency check failed" in response.json()["detail"]


@respx.mock
def test_create_order_idempotency_success_and_duplicate(client, clear_idempotency_set, mock_asyncio_sleep):
    payload = {
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 100.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2",
    }
    ts = str(int(time.time()))
    headers = {"X-Api-Ts": ts}

    setup_respx_quotes(respx.mock)
    setup_respx_executes(respx.mock, status="success")

    # First request
    response1 = client.post("/orders", json=payload, headers=headers)
    assert response1.status_code == 200

    # Second request with same headers and payload (same hash)
    response2 = client.post("/orders", json=payload, headers=headers)
    assert response2.status_code == 400
    assert "Idempotency check failed" in response2.json()["detail"]


def test_create_order_validation_fail(client, clear_idempotency_set, mock_asyncio_sleep):
    response = client.post(
        "/orders",
        json={
            "direction": "on-ramp",
            "pair": "USDT-USD",
            "amount": 1001.0,
            "incoming_account": "acct-1",
            "outgoing_account": "acct-2",
        },
        headers={"X-Api-Ts": "12345"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Not allowed, amount over the limit"


@respx.mock
def test_create_order_validation_success(client, clear_idempotency_set, mock_asyncio_sleep):
    payload = {
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 1000.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2",
    }

    setup_respx_quotes(respx.mock)
    setup_respx_executes(respx.mock, status="success")

    response = client.post(
        "/orders",
        json=payload,
        headers={"X-Api-Ts": "12345"},
    )
    assert response.status_code == 200
