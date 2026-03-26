import httpx
import pytest
from lib.http_client import LoggingAsyncClient


@pytest.mark.asyncio
async def test_httpx_logging_transport(capsys, configure_logging):
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
async def test_httpx_error_logging(capsys, configure_logging):
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
