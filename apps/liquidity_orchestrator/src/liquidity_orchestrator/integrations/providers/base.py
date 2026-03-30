from abc import ABC, abstractmethod
from typing import Awaitable

import httpx
from liquidity_orchestrator.domain.enums import ProviderExecutionStatus
from liquidity_orchestrator.domain.interfaces import IProvider
from liquidity_orchestrator.domain.provider_dto import (
    ProviderExecutionResponse,
    ProviderGetQuoteRequest,
    ProviderOrderExecutionRequest,
    ProviderQuoteResponse,
)


class BaseProvider(IProvider, ABC):
    httpx_client: httpx.AsyncClient

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
