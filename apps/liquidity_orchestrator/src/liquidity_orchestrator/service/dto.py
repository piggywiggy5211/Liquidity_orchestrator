from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field

from liquidity_orchestrator.domain.enums import OrderStatus, QuoteDirection


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)


class OrderCreateDTO(BaseDTO):
    direction: QuoteDirection
    pair: str
    amount: Decimal
    incoming_account: str
    outgoing_account: str


class OrderDTO(BaseDTO):
    id: int
    status: OrderStatus
    direction: QuoteDirection
    pair: str
    incoming_amount: Decimal
    incoming_account: str
    outgoing_amount: Decimal
    outgoing_account: str
    created_at: datetime
    version: int = 0

    @computed_field
    def commission_amount(self) -> Decimal | None:
        if self.incoming_amount is not None and self.outgoing_amount is not None:
            return self.incoming_amount - self.outgoing_amount
        return None


class QuoteDTO(BaseDTO):
    fee_rate: Decimal
    provider_name: str
    amount_in: Decimal
    direction: QuoteDirection | None = None
    pair: str | None = None
    amount_out: Decimal | None = None
    valid_until: datetime | None = None
    id: int | None = None
