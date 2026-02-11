import httpx
from loguru import logger


class LoggingTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport: httpx.AsyncBaseTransport):
        self._transport = transport

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        # sanitize headers for logging only (case-insensitive removal of Authorization)
        headers = {k: v for k, v in request.headers.items() if k.lower() != "authorization"}

        # avoid consuming request stream; use content if readily available
        body_bytes = request.content if request.content is not None else b""
        body_data = body_bytes.decode(errors="replace")

        # log_message format as requested
        request_name = request.method
        log_message = (
            f"HTTP {request_name}"
            f"\n URL: {url}"
            f"\n HEADERS: {headers}"
            f"\n BODY RAW: {body_data}"
        )
        logger.info(log_message)

        try:
            response = await self._transport.handle_async_request(request)

            response_body = await response.aread()
            response_body_decoded = response_body.decode(errors="replace")

            log_message_resp = (
                f"HTTP RESPONSE {response.status_code}"
                f"\n URL: {url}"
                f"\n HEADERS: {dict(response.headers)}"
                f"\n BODY RAW: {response_body_decoded}"
            )
            logger.info(log_message_resp)
            return response
        except httpx.TimeoutException as exc:
            logger.error(f"HTTP {request_name} TIMEOUT\n URL: {url}\n ERROR: {str(exc)}")
            raise
        except httpx.ConnectError as exc:
            logger.error(f"HTTP {request_name} CONNECTION ERROR\n URL: {url}\n ERROR: {str(exc)}")
            raise
        except Exception as exc:
            logger.error(f"HTTP {request_name} ERROR\n URL: {url}\n ERROR: {str(exc)}")
            raise


def create_http_client() -> httpx.AsyncClient:
    base_transport = httpx.AsyncHTTPTransport(retries=1)
    logging_transport = LoggingTransport(base_transport)
    return httpx.AsyncClient(transport=logging_transport)
