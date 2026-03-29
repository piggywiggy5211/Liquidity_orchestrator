from datetime import datetime
from decimal import Decimal
from enum import Enum

from liquidity_orchestrator.domain.enums import QuoteDirection
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    DECLINE = "decline"
    TIMEOUT = "timeout"


class OrderExecutionRequest(BaseModel):
    direction: QuoteDirection
    pair: str = Field(
        ...,
        pattern=r"^[a-zA-Z]+-[a-zA-Z]+$",
        description="Asset pair in format 'USDT-USD'",
    )
    amount: Decimal
    incoming_account: str
    outgoing_account: str


class GetQuoteRequest(BaseModel):
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
    status: ExecutionStatus
    provider_ref: str | None
