import httpx
from liquidity_orchestrator.core.config import settings
from liquidity_orchestrator.domain.enums import ProviderExecutionStatus
from liquidity_orchestrator.domain.interfaces import IProvider
from liquidity_orchestrator.domain.provider_dto import (
    ProviderExecutionResponse,
    ProviderGetQuoteRequest,
    ProviderOrderExecutionRequest,
    ProviderQuoteResponse,
)


class ProviderC(IProvider):
    name = "ProviderC"

    async def get_quote(self, request: ProviderGetQuoteRequest) -> ProviderQuoteResponse:
        params = {
            "direction": request.direction,
            "pair": request.pair,
            "amount_out": str(request.amount_out),
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.mock_provider_url}/provider_c/quote", params=params)
            response.raise_for_status()
            return ProviderQuoteResponse.model_validate(response.json())

    async def execute(self, order: ProviderOrderExecutionRequest) -> ProviderExecutionResponse:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.mock_provider_url}/provider_c/execute",
                    json={
                        "direction": order.direction,
                        "pair": order.pair,
                        "amount": str(order.amount),
                        "incoming_account": order.incoming_account,
                        "outgoing_account": order.outgoing_account,
                    },
                )
                response.raise_for_status()
                return ProviderExecutionResponse.model_validate(response.json())
        except httpx.ReadTimeout:
            return ProviderExecutionResponse(status=ProviderExecutionStatus.TIMEOUT, provider_ref=None)
        except Exception:
            return ProviderExecutionResponse(status=ProviderExecutionStatus.DECLINE, provider_ref=None)
