from typing import Protocol

from liquidity_orchestrator.integrations.dto import (
    GetQuoteRequest,
    OrderExecutionRequest,
    ProviderExecutionResponse,
    ProviderQuoteResponse,
)


class IProvider(Protocol):
    name: str

    async def get_quote(self, request: GetQuoteRequest) -> ProviderQuoteResponse: ...

    async def execute(self, order: OrderExecutionRequest) -> ProviderExecutionResponse: ...
