import httpx
from loguru import logger

from app.core.logger.sanitizer import sanitize_headers


class LoggingTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport: httpx.AsyncBaseTransport):
        self._transport = transport

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        await self._log_request(request)
        try:
            response = await self._transport.handle_async_request(request)
            await self._log_response(request, response)
            return response
        except Exception as exc:
            self._log_error(request, exc)
            raise

    @staticmethod
    async def _log_request(request: httpx.Request):
        url = str(request.url)
        headers = sanitize_headers(request.headers)
        query_params = dict(request.url.params)
        body_bytes = request.content if request.content is not None else b""
        body_data_decoded = body_bytes.decode(errors="replace")
        method = request.method

        log_message = (
            f"HTTPX CLIENT REQUEST"
            f" {method}"
            f" URL: {url}"
        )
        logger.bind(
            request_details={
                "method": method,
                "url": url,
                "headers": headers,
                "query_params": query_params,
                "body_raw": body_data_decoded,
            },
        ).info(log_message)

    @staticmethod
    async def _log_response(request: httpx.Request, response: httpx.Response):
        url = str(request.url)
        status_code = response.status_code
        headers = sanitize_headers(response.headers)
        body_bytes = await response.aread()
        body_data_decoded = body_bytes.decode(errors="replace")
        method = request.method

        log_message = (
            f"HTTPX CLIENT RESPONSE"
            f" {method}"
            f" STATUS_CODE: {status_code}"
            f" URL: {url}"
        )

        logger.bind(
            response_details={
                "status_code": status_code,
                "url": url,
                "headers": headers,
                "body_raw": body_data_decoded,
            },
        ).info(log_message)

    @staticmethod
    def _log_error(request: httpx.Request, exc: Exception):
        url = str(request.url)
        request_name = request.method
        match exc:
            case httpx.TimeoutException():
                logger.error(f"HTTP {request_name} TIMEOUT\n URL: {url}\n ERROR: {str(exc)}")
            case httpx.ConnectError():
                logger.error(f"HTTP {request_name} CONNECTION ERROR\n URL: {url}\n ERROR: {str(exc)}")
            case _:
                logger.error(f"HTTP {request_name} ERROR\n URL: {url}\n ERROR: {str(exc)}")


def create_http_client() -> httpx.AsyncClient:
    base_transport = httpx.AsyncHTTPTransport(retries=1)
    logging_transport = LoggingTransport(base_transport)
    return httpx.AsyncClient(transport=logging_transport)
