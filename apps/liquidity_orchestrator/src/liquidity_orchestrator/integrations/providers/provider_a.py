from liquidity_orchestrator.domain.provider_dto import (
    ProviderExecutionResponse,
    ProviderGetQuoteRequest,
    ProviderOrderExecutionRequest,
    ProviderQuoteResponse,
)

from .base import BaseProvider


class ProviderA(BaseProvider):
    name = "ProviderA"

    async def get_quote(self, request: ProviderGetQuoteRequest) -> ProviderQuoteResponse:
        params = {
            "direction": request.direction,
            "pair": request.pair,
            "amount_out": str(request.amount_out),
        }

        response = await self.httpx_client.get(f"{self.mock_provider_url}/provider_a/quote", params=params)
        response.raise_for_status()
        return ProviderQuoteResponse.model_validate(response.json())

    async def execute(self, order: ProviderOrderExecutionRequest) -> ProviderExecutionResponse:
        request_coro = self.httpx_client.post(
            f"{self.mock_provider_url}/provider_a/execute",
            json={
                "direction": order.direction,
                "pair": order.pair,
                "amount": str(order.amount),
                "incoming_account": order.incoming_account,
                "outgoing_account": order.outgoing_account,
            },
        )
        return await self._safe_execute(request_coro)
