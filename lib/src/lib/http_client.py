import httpx
from loguru import logger

from lib.sanitizers.http_saitazer import sanitize_headers


async def _log_request(request: httpx.Request):
    url = str(request.url)
    headers = sanitize_headers(request.headers)
    query_params = dict(request.url.params)
    body_bytes = request.content if request.content is not None else b""
    body_data_decoded = body_bytes.decode(errors="replace")
    method = request.method

    log_message = f"HTTPX CLIENT REQUEST {method} URL: {url}"
    logger.bind(
        request_details={
            "method": method,
            "url": url,
            "headers": headers,
            "query_params": query_params,
            "body_raw": body_data_decoded,
        },
    ).info(log_message)


async def _log_response(response: httpx.Response):
    request = response.request
    url = str(request.url)
    status_code = response.status_code
    headers = sanitize_headers(response.headers)
    body_bytes = await response.aread()
    body_data_decoded = body_bytes.decode(errors="replace")
    method = request.method

    log_message = f"HTTPX CLIENT RESPONSE {method} STATUS_CODE: {status_code} URL: {url}"

    logger.bind(
        response_details={
            "status_code": status_code,
            "url": url,
            "headers": headers,
            "body_raw": body_data_decoded,
        },
    ).info(log_message)


class LoggingAsyncClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        event_hooks = kwargs.pop("event_hooks", {})

        if "response" not in event_hooks:
            event_hooks["response"] = list()
        if "request" not in event_hooks:
            event_hooks["request"] = list()

        event_hooks["response"].append(_log_response)
        event_hooks["request"].append(_log_request)

        super().__init__(*args, event_hooks=event_hooks, **kwargs)

    async def send(self, request: httpx.Request, **kwargs) -> httpx.Response:
        try:
            return await super().send(request, **kwargs)
        except Exception as exc:
            self._log_error(request, exc)
            raise

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
    return LoggingAsyncClient()
