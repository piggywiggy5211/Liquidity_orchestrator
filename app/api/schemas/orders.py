from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.api.schemas.base import Base
from app.service.enums import QuoteDirection


class OrderCreateRequest(Base):
    direction: QuoteDirection
    pair: str = Field(
        ...,
        pattern=r"^[a-zA-Z]+-[a-zA-Z]+$",
        description="Asset pair in format 'USDT-USD'",
    )
    amount: Decimal
    incoming_account: str
    outgoing_account: str

    @field_validator("pair", mode="before")
    @classmethod
    def uppercase_pair(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v


class OrderResponse(Base):
    id: int
    status: str
    direction: QuoteDirection
    pair: str
    incoming_amount: Decimal
    incoming_account: str
    outgoing_amount: Decimal
    outgoing_account: str
    commission_amount: Decimal
    created_at: datetime
