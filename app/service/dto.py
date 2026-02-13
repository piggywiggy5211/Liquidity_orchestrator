from dataclasses import dataclass
from decimal import Decimal
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
