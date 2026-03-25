from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable

from loguru import logger
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def get_current_trace_id() -> str:
    trace_id = trace.get_current_span().get_span_context().trace_id
    # Trace ID int -> The traceID as 32-byte hexadecimal string
    hex_trace_id = format(trace_id, "032x")
    return hex_trace_id


def get_current_span_id() -> str:
    span_id = trace.get_current_span().get_span_context().span_id
    hex_span_id = format(span_id, "016x")
    return hex_span_id


@asynccontextmanager
async def trace_id_context_logged() -> AsyncGenerator[None, None]:
    trace_id = get_current_trace_id()
    span_id = get_current_span_id()
    with logger.contextualize(trace_id=trace_id, span_id=span_id):
        yield


class LoggerContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        async with trace_id_context_logged():
            response = await call_next(request)
            return response
