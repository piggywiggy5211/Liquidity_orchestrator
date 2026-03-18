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
