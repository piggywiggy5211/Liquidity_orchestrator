from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from dataclasses import dataclass, field
from .enums import OrderStatus, QuoteDirection, OutboxEventType

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
