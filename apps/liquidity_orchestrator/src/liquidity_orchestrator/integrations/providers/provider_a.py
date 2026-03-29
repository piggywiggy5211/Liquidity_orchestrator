import httpx
from liquidity_orchestrator.core.config import settings
from liquidity_orchestrator.integrations.dto import (
    ExecutionStatus,
    GetQuoteRequest,
    OrderExecutionRequest,
    ProviderExecutionResponse,
    ProviderQuoteResponse,
)
from liquidity_orchestrator.integrations.interfaces import IProvider


class ProviderA(IProvider):
    name = "ProviderA"

    async def get_quote(self, request: GetQuoteRequest) -> ProviderQuoteResponse:
        params = {
            "direction": request.direction,
            "pair": request.pair,
            "amount_out": str(request.amount_out),
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.mock_provider_url}/provider_a/quote", params=params)
            response.raise_for_status()
            return ProviderQuoteResponse(**response.json())

    async def execute(self, order: OrderExecutionRequest) -> ProviderExecutionResponse:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.mock_provider_url}/provider_a/execute",
                    json={
                        "direction": order.direction,
                        "pair": order.pair,
                        "amount": str(order.amount),
                        "incoming_account": order.incoming_account,
                        "outgoing_account": order.outgoing_account,
                    },
                )
                response.raise_for_status()
                data = response.json()
                status = ExecutionStatus.SUCCESS if data["status"] == "SUCCESS" else ExecutionStatus.DECLINE
                return ProviderExecutionResponse(status=status, provider_ref=data["provider_ref"])
        except httpx.ReadTimeout:
            return ProviderExecutionResponse(status=ExecutionStatus.TIMEOUT, provider_ref=None)
        except Exception:
            return ProviderExecutionResponse(status=ExecutionStatus.DECLINE, provider_ref=None)
