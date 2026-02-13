from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.api.schemas.base import Base
from app.service.enums import QuoteDirection


class QuoteRequest(Base):
    direction: QuoteDirection
    pair: str = Field(
        pattern=r"^[a-zA-Z]+-[a-zA-Z]+$",
        description="Asset pair in format 'USDT-USD'",
    )
    amount: Decimal

    @field_validator("pair", mode="before")
    @classmethod
    def uppercase_pair(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v

class QuoteResponse(Base):
    incoming_amount: str
    incoming_asset_code: str
    outgoing_amount: str
    outgoing_asset_code: str
    fee_amount: str
    fee_asset_code: str
