from datetime import datetime
from decimal import Decimal
from typing import Any

from domain.enums import OrderStatus, OutboxEventType, QuoteDirection
from pydantic import BaseModel, ConfigDict, computed_field


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)


class QuoteRequestDTO(BaseDTO):
    direction: QuoteDirection
    pair: str  # asset pair in format 'USDT-USD'
    amount: Decimal


class QuoteResultDTO(BaseDTO):
    incoming_amount: Decimal | None = None
    incoming_asset_code: str | None = None
    outgoing_amount: Decimal | None = None
    outgoing_asset_code: str | None = None
    fee_amount: Decimal | None = None
    fee_asset_code: str | None = None


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


class OutboxDTO(BaseDTO):
    order_id: int | None = None
    event_type: OutboxEventType | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime | None = None
    id: int | None = None
