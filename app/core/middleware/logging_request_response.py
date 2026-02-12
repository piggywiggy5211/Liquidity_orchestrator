from typing import Callable

from loguru import logger
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.sanitizers.http_saitazer import sanitize_headers


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        await self._log_request(request)
        response = await call_next(request)
        await self._log_response(response, request)
        return response

    @staticmethod
    async def _log_request(request: Request) -> None:
        url = str(request.url)
        headers = sanitize_headers(request.headers)
        query_params = dict(request.query_params)
        body_bytes = await request.body()
        body_data_decoded = body_bytes.decode('utf-8')
        method = request.method

        log_message = (
            f"APP HTTP REQUEST "
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

        async def receive():
            return {"type": "http.request", "body": body_bytes}

        request._receive = receive

    @staticmethod
    async def _log_response(response: Response, request: Request) -> None:
        response_body = [chunk async for chunk in response.body_iterator]  # type: ignore[attr-defined]
        response.body_iterator = iterate_in_threadpool(iter(response_body))  # type: ignore[attr-defined]

        url = str(request.url)
        status_code = response.status_code
        headers = sanitize_headers(response.headers)
        method = request.method
        body_data_decoded = response_body[0].decode() if response_body else None,

        log_message = (
            f"APP HTTP RESPONSE"
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
