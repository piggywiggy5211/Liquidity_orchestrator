from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from liquidity_orchestrator.domain.enums import ProviderExecutionStatus, QuoteDirection


class ProviderOrderExecutionRequest(BaseModel):
    direction: QuoteDirection
    pair: str = Field(
        ...,
        pattern=r"^[a-zA-Z]+-[a-zA-Z]+$",
        description="Asset pair in format 'USDT-USD'",
    )
    amount: Decimal
    incoming_account: str
    outgoing_account: str


class ProviderGetQuoteRequest(BaseModel):
    direction: QuoteDirection
    pair: str = Field(
        ...,
        pattern=r"^[a-zA-Z]+-[a-zA-Z]+$",
        description="Asset pair in format 'USDT-USD'",
    )
    amount_out: Decimal


class ProviderQuoteResponse(BaseModel):
    direction: QuoteDirection
    pair: str
    amount_in: Decimal
    amount_out: Decimal
    fee_rate: Decimal
    valid_until: datetime


class ProviderExecutionResponse(BaseModel):
    status: ProviderExecutionStatus
    provider_ref: str | None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value: Any) -> ProviderExecutionStatus | Any:
        if isinstance(value, str):
            if value == "SUCCESS":
                return ProviderExecutionStatus.SUCCESS
            if value == "DECLINE":
                return ProviderExecutionStatus.DECLINE
        return value
