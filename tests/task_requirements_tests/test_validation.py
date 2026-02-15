import pytest
from fastapi.testclient import TestClient
from app.main import main_app

@pytest.fixture
def client():
    with TestClient(main_app) as c:
        yield c

def test_create_order_validation_fail(client):
    response = client.post("/orders", json={
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 1001.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Not allowed, amount over the limit"

def test_create_order_validation_success(client, clean_db):
    response = client.post("/orders", json={
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 1000.0,
        "incoming_account": "acct-1",
        "outgoing_account": "acct-2"
    })
    assert response.status_code == 200

def test_calculate_quote_validation_fail(client):
    response = client.get("/orders/calculate-quote", params={
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 1000.01
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Not allowed, amount over the limit"

def test_calculate_quote_validation_success(client):
    response = client.get("/orders/calculate-quote", params={
        "direction": "on-ramp",
        "pair": "USDT-USD",
        "amount": 1000.0
    })
    assert response.status_code == 200
