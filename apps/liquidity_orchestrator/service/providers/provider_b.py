from decimal import Decimal
from typing import Any

import httpx
from core.config import settings
from domain.enums import QuoteDirection

from .base import BaseProvider, ExecutionStatus, OrderExecutionRequest


class ProviderB(BaseProvider):
    async def get_quote(
        self,
        direction: QuoteDirection,
        pair: str,
        amount_out: Decimal,
    ) -> dict[str, Any]:
        params = {
            "direction": direction,
            "pair": pair,
            "amount_out": str(amount_out),
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.mock_provider_url}/provider_b/quote", params=params, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            data["fee_rate"] = Decimal(str(data["fee_rate"]))
            data["amount_in"] = Decimal(str(data["amount_in"]))
            data["amount_out"] = Decimal(str(data["amount_out"]))
            return data

    async def execute(self, order: OrderExecutionRequest) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.mock_provider_url}/provider_b/execute",
                    json={
                        "direction": order.direction,
                        "pair": order.pair,
                        "amount": str(order.amount),
                        "incoming_account": order.incoming_account,
                        "outgoing_account": order.outgoing_account,
                    },
                    timeout=2.0,
                )
                response.raise_for_status()
                data = response.json()
                status = ExecutionStatus.SUCCESS if data["status"] == "SUCCESS" else ExecutionStatus.DECLINE
                return {"status": status, "provider_ref": data["provider_ref"]}
        except httpx.ReadTimeout:
            return {"status": ExecutionStatus.TIMEOUT, "provider_ref": None}
        except Exception:
            return {"status": ExecutionStatus.DECLINE, "provider_ref": None}
