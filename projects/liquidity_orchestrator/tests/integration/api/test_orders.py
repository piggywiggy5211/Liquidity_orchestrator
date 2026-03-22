import time


def test_create_order_endpoint(client, mock_asyncio_sleep, clear_idempotency_set):
    response = client.post(
        "/orders",
        json={
            "direction": "on-ramp",
            "pair": "USDT-USD",
            "amount": 100.0,
            "incoming_account": "acct-1",
            "outgoing_account": "acct-2",
        },
        headers={"X-Api-Ts": "12345"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "NEW"
    assert data["incoming_account"] == "acct-1"


def test_create_and_get_order(client, clear_idempotency_set, mock_asyncio_sleep):
    # 1. Create order
    payload = {
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 100.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2",
    }
    headers = {"X-Api-Ts": "12345"}
    create_resp = client.post("/orders", json=payload, headers=headers)
    assert create_resp.status_code == 200
    order_id = create_resp.json()["id"]

    # 2. Get order
    get_resp = client.get(f"/orders/{order_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == order_id
    assert data["incoming_account"] == "acct-1"
    assert data["pair"] == "USDT-USD"


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


def test_create_order_validation_success(client, clear_idempotency_set, mock_asyncio_sleep):
    response = client.post(
        "/orders",
        json={
            "direction": "on-ramp",
            "pair": "USDT-USD",
            "amount": 1000.0,
            "incoming_account": "acct-1",
            "outgoing_account": "acct-2",
        },
        headers={"X-Api-Ts": "12345"},
    )
    assert response.status_code == 200
