from fastapi.testclient import TestClient

from mock_providers.main import app


client = TestClient(app)


def test_provider_a_quote():
    response = client.get("/provider_a/quote", params={"direction": "on-ramp", "pair": "USDT-USD", "amount_out": 100})
    assert response.status_code == 200
    data = response.json()
    assert data["pair"] == "USDT-USD"
    assert data["direction"] == "on-ramp"
    assert "fee_rate" in data
    assert "amount_out" in data


def test_provider_a_execute():
    response = client.post(
        "/provider_a/execute",
        json={
            "direction": "on-ramp",
            "pair": "USDT-USD",
            "amount": "100.5",
            "incoming_account": "acc1",
            "outgoing_account": "acc2",
        },
    )
    # Will timeout sometimes, but test client doesn't actually timeout, it just waits.
    # The server might sleep 10s if rand hits the timeout prob.
    # To make tests fast, we could mock `random.random`, but for simple integration, we just let it run.
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["SUCCESS", "DECLINE"]
    assert "provider_ref" in data
