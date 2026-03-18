from decimal import Decimal

from pydantic import Field, field_validator

from app.domain.enums import QuoteDirection
from app.entrypoints.fastapi.api.schemas.base import Base


class QuoteRequest(Base):
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

    @field_validator("pair", mode="before")
    @classmethod
    def uppercase_pair(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v


class QuoteResponse(Base):
    incoming_amount: Decimal = Field(
        ...,
        examples=[100],
    )
    incoming_asset_code: str
    outgoing_amount: Decimal = Field(
        ...,
        examples=[98],
    )
    outgoing_asset_code: str
    fee_amount: Decimal = Field(
        ...,
        examples=[2],
    )
    fee_asset_code: str
