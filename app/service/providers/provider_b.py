from decimal import Decimal
from typing import Optional, Any
from .base import BaseProvider, OrderExecutionRequest, ExecutionStatus
from app.service.enums import QuoteDirection

class ProviderB(BaseProvider):
    async def get_quote(
        self, 
        direction: QuoteDirection, 
        pair: str, 
        amount_in: Optional[Decimal] = None, 
        amount_out: Optional[Decimal] = None
    ) -> Any:
        # Stub implementation for ProviderB
        return {
            "provider": "ProviderB",
            "pair": pair,
            "direction": direction,
            "amount_in": amount_in,
            "amount_out": amount_out
        }

    async def execute(self, order: OrderExecutionRequest) -> dict:
        # Stub implementation for ProviderB
        return {
            "status": ExecutionStatus.SUCCESS,
            "provider_ref": "ref-b-456"
        }
