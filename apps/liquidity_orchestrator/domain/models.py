from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from .enums import OrderStatus, OutboxEventType, QuoteDirection


@dataclass
class Order:
    incoming_amount: Decimal
    outgoing_amount: Decimal
    incoming_account: str
    outgoing_account: str
    direction: QuoteDirection
    pair: str
    created_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None
    quote_id: Optional[str] = None
    status: OrderStatus = OrderStatus.NEW
    provider_ref: Optional[str] = None
    updated_at: Optional[datetime] = None
    version: int = 0

    @classmethod
    def create(
        cls,
        amount: Decimal,
        direction: QuoteDirection,
        pair: str,
        incoming_account: str,
        outgoing_account: str,
        commission_rate: Decimal,
    ) -> "Order":
        commission_amount = amount * commission_rate
        target_amount_out = amount - commission_amount
        return cls(
            incoming_amount=amount,
            outgoing_amount=target_amount_out,
            direction=direction,
            pair=pair,
            incoming_account=incoming_account,
            outgoing_account=outgoing_account,
        )


@dataclass
class Quote:
    direction: QuoteDirection
    pair: str
    amount_in: Decimal
    amount_out: Decimal
    fee_rate: Decimal
    provider_name: str
    valid_until: datetime
    id: Optional[int] = None


@dataclass
class Outbox:
    order_id: int
    event_type: OutboxEventType
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None
