from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from dataclasses import dataclass
from .enums import OrderStatus, QuoteDirection, OutboxEventType

@dataclass
class Order:
    amount: Decimal
    incoming_account: str
    outgoing_account: str
    direction: QuoteDirection
    pair: str
    provider_name: Optional[str] = None
    id: Optional[int] = None
    quote_id: Optional[str] = None
    status: OrderStatus = OrderStatus.NEW
    provider_ref: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Quote:
    direction: QuoteDirection
    pair: str
    amount_in: Decimal
    amount_out: Decimal
    amount_fee: Decimal
    provider_name: str
    valid_until: datetime
    id: Optional[int] = None

@dataclass
class Outbox:
    order_id: int
    event_type: OutboxEventType
    payload: dict[str, Any]
    id: Optional[int] = None
    created_at: Optional[datetime] = None
