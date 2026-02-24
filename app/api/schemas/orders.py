from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.api.schemas.base import Base
from app.service.enums import QuoteDirection


class OrderCreateRequest(Base):
    direction: QuoteDirection
    pair: str = Field(
        ...,
        pattern=r"^[a-zA-Z]{3,4}-[a-zA-Z]{3,4}$",
        description="Asset pair in format 'USDT-USD'",
        examples=["USDT-USD", "USD-USDT"],
    )
    amount: Decimal = Field(
        ...,
        examples=[100, 150],
    )
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
    incoming_amount: Decimal = Field(
        ...,
        examples=[100],
    )
    incoming_account: str
    outgoing_amount: Decimal = Field(
        ...,
        examples=[98],
    )
    outgoing_account: str
    commission_amount: Decimal = Field(
        ...,
        examples=[2],
    )
    created_at: datetime
