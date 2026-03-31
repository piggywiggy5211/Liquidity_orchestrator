import time
from abc import ABC, abstractmethod
from functools import wraps
from typing import TYPE_CHECKING, Any, Awaitable, Callable

import httpx
from liquidity_orchestrator.domain.enums import ProviderExecutionStatus
from liquidity_orchestrator.domain.interfaces import IProvider
from liquidity_orchestrator.domain.provider_dto import (
    ProviderExecutionResponse,
    ProviderGetQuoteRequest,
    ProviderOrderExecutionRequest,
    ProviderQuoteResponse,
)


if TYPE_CHECKING:
    from liquidity_orchestrator.domain.interfaces import IMetricsCollector


def with_metrics(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> ProviderExecutionResponse:
        start_time = time.perf_counter()
        status = None
        try:
            response = await func(self, *args, **kwargs)
            if hasattr(response, "status"):
                status = response.status
            return response
        finally:
            latency = time.perf_counter() - start_time
            metrics_collector = getattr(self, "metrics_collector", None)
            if metrics_collector:
                metrics_collector.record_execution(self.name, latency, status)

    return wrapper


class BaseProvider(IProvider, ABC):
    httpx_client: httpx.AsyncClient
    metrics_collector: "IMetricsCollector"
    mock_provider_url: str

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "execute" in cls.__dict__:
            original_execute = cls.__dict__["execute"]
            if callable(original_execute):
                setattr(cls, "execute", with_metrics(original_execute))

    @abstractmethod
    async def get_quote(self, request: ProviderGetQuoteRequest) -> ProviderQuoteResponse: ...

    @abstractmethod
    async def execute(self, order: ProviderOrderExecutionRequest) -> ProviderExecutionResponse: ...

    async def _safe_execute(self, request_coro: Awaitable[httpx.Response]) -> ProviderExecutionResponse:
        try:
            response = await request_coro
            response.raise_for_status()
            return ProviderExecutionResponse.model_validate(response.json())
        except httpx.ReadTimeout:
            return ProviderExecutionResponse(status=ProviderExecutionStatus.TIMEOUT, provider_ref=None)
        except Exception:
            return ProviderExecutionResponse(status=ProviderExecutionStatus.DECLINE, provider_ref=None)
