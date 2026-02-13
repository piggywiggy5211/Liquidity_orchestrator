from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from .enums import QuoteDirection

@dataclass(frozen=True)
class QuoteGetDTO:
    direction: QuoteDirection
    pair: str  # asset pair in format 'USDT-USD'
    amount: Decimal

@dataclass(frozen=True)
class QuoteResultDTO:
    incoming_amount: Decimal
    incoming_asset_code: str
    outgoing_amount: Decimal
    outgoing_asset_code: str
    fee_amount: Decimal
    fee_asset_code: str

@dataclass(frozen=True)
class OrderCreateDTO:
    direction: QuoteDirection
    pair: str
    amount: Decimal
    incoming_account: str
    outgoing_account: str

@dataclass(frozen=True)
class OrderResultDTO:
    id: str
    status: str
    direction: QuoteDirection
    pair: str
    incoming_amount: Decimal
    incoming_account: str
    outgoing_amount: Decimal
    outgoing_account: str
    commission_amount: Decimal
    created_at: datetime
