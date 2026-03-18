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


def test_calculate_quote_validation_fail(client):
    response = client.get("/calculate-quote", params={"direction": "on-ramp", "pair": "USDT-USD", "amount": 1000.01})
    assert response.status_code == 422
    assert response.json()["detail"] == "Not allowed, amount over the limit"


def test_calculate_quote_validation_success(client):
    response = client.get("/calculate-quote", params={"direction": "on-ramp", "pair": "USDT-USD", "amount": 1000.0})
    assert response.status_code == 200
