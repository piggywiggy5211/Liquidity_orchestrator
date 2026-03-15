import pytest
from fastapi.testclient import TestClient

from app.main import main_app


@pytest.fixture
def client():
    with TestClient(main_app) as c:
        yield c


def test_get_order_success(client):
    # 1. Create an order
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

    # 2. Get the order
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
