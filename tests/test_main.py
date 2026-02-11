import pytest
import json
import httpx
from fastapi.testclient import TestClient
from app.main import main_app
from app.core.logger.sanitizer import mask_iban
from app.core.logger.loguru_logger import serialize_json_log
from app.services.liquidity import LiquidityService
from app.schemas.orders import OrderCreate, QuoteRequest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def client():
    with TestClient(main_app) as c:
        yield c

def test_mask_iban():
    iban = "DE12345678901234567890"
    masked = mask_iban(iban)
    assert masked.startswith("DE12")
    assert masked.endswith("7890")
    assert "*" in masked

def test_log_sanitizer_multiple_rules():
    from app.core.logger.sanitizer import LogSanitizer
    s = LogSanitizer()
    # Add a dummy rule
    s.add_sanitizer(lambda x: x.replace("SECRET", "******"))
    
    text = "IBAN: DE12345678901234567890 and SECRET value"
    sanitized = s.sanitize(text)
    
    assert "DE12****7890" in sanitized
    assert "******" in sanitized
    assert "SECRET" not in sanitized

def test_json_logging_format():
    record = {
        "time": MagicMock(),
        "level": MagicMock(name="INFO"),
        "message": "test message with IBAN DE12345678901234567890",
        "extra": {
            "trace_id": "1234567890",
            "span_id": "0987654321"
        },
        "exception": None
    }
    record["time"].strftime.return_value = "2026-02-10T14:30:15.123Z"
    record["level"].name = "INFO"
    
    log_json = serialize_json_log(record)
    data = json.loads(log_json)
    
    assert data["service"] == "liquidity-orchestrator"
    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert "DE12****7890" in data["message"]
    assert "trace_id" in data

def test_create_order_endpoint(client):
    response = client.post("/create_order", json={
        "amount": 100.0,
        "currency": "USD",
        "destination_address": "0x123"
    })
    assert response.status_code == 200
    assert response.json() == {"id": "ord_12345", "status": "pending"}


def test_get_quote_endpoint(client):
    response = client.get("/get_quote", params={
        "from_currency": "USD",
        "to_currency": "EUR",
        "amount": 100.0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["quote_id"] == "qt_67890"
    assert data["rate"] == 0.95
    assert data["estimated_amount"] == 95.0

@pytest.mark.asyncio
async def test_liquidity_service():
    mock_db = AsyncMock()
    mock_http = AsyncMock()
    service = LiquidityService(mock_db, mock_http)
    
    order = OrderCreate(amount=100.0, currency="USD", destination_address="0x123")
    res = await service.create_order(order)
    assert res.id == "ord_12345"
    
    quote = QuoteRequest(from_currency="USD", to_currency="EUR", amount=100.0)
    res_q = await service.get_quote(quote)
    assert res_q.quote_id == "qt_67890"

@pytest.mark.asyncio
async def test_httpx_logging_transport(capsys):
    from app.core.http_client import LoggingTransport

    class DummyTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                headers={"content-type": "application/json"},
                content=b'{"status": "ok"}',
                request=request,
            )

    inner = DummyTransport()
    transport = LoggingTransport(inner)

    request = httpx.Request(
        "POST",
        "https://api.example.com/test",
        headers={"Authorization": "Bearer token", "X-Test": "val"},
        content=b"some body",
    )

    resp = await transport.handle_async_request(request)

    assert resp.status_code == 200

    out = capsys.readouterr().out
    # Logs are JSON lines; ensure our transport messages are present and header Authorization is removed
    assert "HTTP POST" in out
    lower_out = out.lower()
    assert "authorization" not in lower_out
    assert "x-test" in lower_out


def test_http_client_in_lifespan():
    # Ensure httpx client is created globally in lifespan
    with TestClient(main_app) as c:
        assert hasattr(c.app.state, "http_client")
        import httpx as _httpx
        assert isinstance(c.app.state.http_client, _httpx.AsyncClient)
