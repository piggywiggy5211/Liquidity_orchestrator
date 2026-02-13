from decimal import Decimal
from typing import Optional, Any
from .base import BaseProvider, OrderExecutionRequest, ExecutionStatus
from app.service.enums import QuoteDirection

class ProviderC(BaseProvider):
    async def get_quote(
        self, 
        direction: QuoteDirection, 
        pair: str, 
        amount_in: Optional[Decimal] = None, 
        amount_out: Optional[Decimal] = None
    ) -> Any:
        # Stub implementation for ProviderC
        return {
            "provider": "ProviderC",
            "pair": pair,
            "direction": direction,
            "amount_in": amount_in,
            "amount_out": amount_out
        }

    async def execute(self, order: OrderExecutionRequest) -> dict:
        # Stub implementation for ProviderC
        return {
            "status": ExecutionStatus.TIMEOUT,
            "provider_ref": None
        }
