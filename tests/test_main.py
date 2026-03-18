import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.http_client import LoggingAsyncClient
from app.core.logger.loguru_logger import serialize_json_log
from app.core.sanitizers.http_saitazer import sanitize_headers
from app.core.sanitizers.log_sanitizer import LogSanitizer, mask_iban
from app.database.uow import UnitOfWorkSqlAlchemy
from app.service.dto import QuoteRequestDTO
from app.service.enums import OrderStatus, QuoteDirection
from app.service.liquidity_service import LiquidityService
from app.service.models import Order
from app.service.providers import ExecutionStatus


def test_mask_iban():
    iban = "DE12345678901234567890"
    masked = mask_iban(iban)
    assert masked.startswith("DE12")
    assert masked.endswith("7890")
    assert "*" in masked


def test_log_sanitizer_multiple_rules():
    s = LogSanitizer()
    # Add a dummy rule
    s.add_sanitizer(lambda x: x.replace("SECRET", "******"))

    text = "IBAN: DE12345678901234567890 and SECRET value"
    sanitized = s.sanitize(text)

    assert "DE12****7890" in sanitized
    assert "******" in sanitized
    assert "SECRET" not in sanitized


def test_sanitize_headers():
    headers = {"Authorization": "Bearer token123", "Content-Type": "application/json", "authorization": "Secret"}
    sanitized = sanitize_headers(headers)
    assert "Authorization" not in sanitized
    assert "authorization" not in sanitized
    assert sanitized["Content-Type"] == "application/json"
    assert len(sanitized) == 1


def test_json_logging_format():
    record = {
        "time": MagicMock(),
        "level": MagicMock(name="INFO"),
        "message": "test message with IBAN DE12345678901234567890",
        "extra": {"trace_id": "1234567890", "span_id": "0987654321"},
        "exception": None,
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


def test_get_quote_endpoint(client):
    # Test with uppercase
    response = client.get("/calculate-quote", params={"direction": "on-ramp", "pair": "EUR-EURS", "amount": 100.0})
    assert response.status_code == 200
    data = response.json()
    assert data["incoming_amount"] == "100.0"
    assert data["incoming_asset_code"] == "EUR"

    # Test with lowercase (should be case-insensitive and auto-uppercased)
    response = client.get("/calculate-quote", params={"direction": "on-ramp", "pair": "eur-eurs", "amount": 100.0})
    assert response.status_code == 200
    data = response.json()
    assert data["incoming_amount"] == "100.0"
    assert data["incoming_asset_code"] == "EUR"
    assert data["outgoing_asset_code"] == "EURS"


@pytest.mark.asyncio
async def test_liquidity_service(db_session, session_factory, mock_asyncio_sleep):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    mock_http = AsyncMock()
    service = LiquidityService(uow, mock_http)

    from app.service.dto import OrderCreateDTO

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="USDT-USD",
        amount=Decimal("100.0"),
        incoming_account="acct-1",
        outgoing_account="acct-2",
    )

    with patch("app.service.providers.base.BaseProvider.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"status": ExecutionStatus.SUCCESS, "provider_ref": "ref-123"}

        created = await service.create_order(order_in)
        assert created.status == "NEW"
        assert created.incoming_amount == Decimal("100.0")
        assert created.outgoing_amount == Decimal("98.0")
        await service.execute_order(int(created.id))

    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.COMPLETED
        assert order.incoming_amount == Decimal("100.0")
        assert order.outgoing_amount == Decimal("98.0")

    quote_dto = QuoteRequestDTO(direction=QuoteDirection.ON_RAMP, pair="EUR-EURS", amount=Decimal("100.0"))
    res_q = await service.get_quote(quote_dto)
    assert res_q.incoming_amount == Decimal("100.0")
    # With default 0.02 fee: 100 - 2 = 98
    assert res_q.outgoing_amount == Decimal("98")


@pytest.mark.asyncio
async def test_httpx_logging_transport(capsys):
    class DummyTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                headers={"content-type": "application/json"},
                content=b'{"status": "ok"}',
                request=request,
            )

    inner = DummyTransport()
    async with LoggingAsyncClient(transport=inner) as client:
        resp = await client.post(
            "https://api.example.com/test",
            headers={"Authorization": "Bearer token", "X-Test": "val"},
            content=b"some body",
        )

    assert resp.status_code == 200

    out = capsys.readouterr().out
    assert "HTTPX CLIENT REQUEST POST URL: https://" in out
    lower_out = out.lower()
    assert "authorization" not in lower_out
    assert "x-test" in lower_out


@pytest.mark.asyncio
async def test_httpx_error_logging(capsys):
    class ErrorTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

    inner = ErrorTransport()
    async with LoggingAsyncClient(transport=inner) as client:
        with pytest.raises(httpx.ConnectError):
            await client.get("https://api.example.com/test")

    out = capsys.readouterr().out
    assert "HTTP GET CONNECTION ERROR" in out
    assert "Connection refused" in out


def test_http_client_in_lifespan(client):
    # Ensure httpx client is created globally in lifespan
    assert hasattr(client.app.state, "http_client")
    import httpx as _httpx

    assert isinstance(client.app.state.http_client, _httpx.AsyncClient)
