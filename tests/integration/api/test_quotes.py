def test_get_quote_endpoint(client):
    # Test with uppercase
    response = client.get("/calculate-quote", params={"direction": "on-ramp", "pair": "EUR-EURS", "amount": 100.0})
    assert response.status_code == 200
    data = response.json()
    assert data["incoming_amount"] == "100.0"
    assert data["incoming_asset_code"] == "EUR"

    # Test with lowercase
    response = client.get("/calculate-quote", params={"direction": "on-ramp", "pair": "eur-eurs", "amount": 100.0})
    assert response.status_code == 200
    data = response.json()
    assert data["incoming_amount"] == "100.0"
    assert data["incoming_asset_code"] == "EUR"
    assert data["outgoing_asset_code"] == "EURS"


def test_calculate_quote_validation_fail(client):
    response = client.get("/calculate-quote", params={"direction": "on-ramp", "pair": "USDT-USD", "amount": 1000.01})
    assert response.status_code == 422
    assert response.json()["detail"] == "Not allowed, amount over the limit"


def test_calculate_quote_validation_success(client):
    response = client.get("/calculate-quote", params={"direction": "on-ramp", "pair": "USDT-USD", "amount": 1000.0})
    assert response.status_code == 200
