from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field
from service.enums import QuoteDirection


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    FAIL = "FAIL"


class QuoteResponse(BaseModel):
    pair: str
    direction: QuoteDirection
    amount_in: Decimal
    amount_out: Decimal
    fee_rate: Decimal
    valid_until: str


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


class ExecuteResponse(BaseModel):
    status: ExecutionStatus
    provider_ref: str
