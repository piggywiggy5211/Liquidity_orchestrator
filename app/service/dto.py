from typing import Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, computed_field
from .enums import QuoteDirection, OrderStatus, OutboxEventType


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)


class QuoteGetDTO(BaseDTO):
    direction: QuoteDirection | None = None
    pair: str | None = None  # asset pair in format 'USDT-USD'
    amount: Decimal | None = None


class QuoteResultDTO(BaseDTO):
    incoming_amount: Decimal | None = None
    incoming_asset_code: str | None = None
    outgoing_amount: Decimal | None = None
    outgoing_asset_code: str | None = None
    fee_amount: Decimal | None = None
    fee_asset_code: str | None = None


class OrderCreateDTO(BaseDTO):
    direction: QuoteDirection | None = None
    pair: str | None = None
    amount: Decimal | None = None
    incoming_account: str | None = None
    outgoing_account: str | None = None


class OrderExecutionResult(BaseDTO):
    order_id: int
    status: OrderStatus
    quote_id: int | None = None
    provider_ref: str | None = None


class OrderDTO(BaseDTO):
    id: int | None = None
    status: OrderStatus | None = None
    direction: QuoteDirection | None = None
    pair: str | None = None
    incoming_amount: Decimal | None = None
    incoming_account: str | None = None
    outgoing_amount: Decimal | None = None
    outgoing_account: str | None = None
    created_at: datetime | None = None
    version: int = 0

    @computed_field
    @property
    def commission_amount(self) -> Decimal | None:
        if self.incoming_amount is not None and self.outgoing_amount is not None:
            return self.incoming_amount - self.outgoing_amount
        return None


class QuoteDTO(BaseDTO):
    direction: QuoteDirection | None = None
    pair: str | None = None
    amount_in: Decimal | None = None
    amount_out: Decimal | None = None
    fee_rate: Decimal | None = None
    provider_name: str | None = None
    valid_until: datetime | None = None
    id: int | None = None


class OutboxDTO(BaseDTO):
    order_id: int | None = None
    event_type: OutboxEventType | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime | None = None
    id: int | None = None
