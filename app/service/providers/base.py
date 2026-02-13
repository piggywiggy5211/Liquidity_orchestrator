from typing import Protocol, Any
from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
from app.service.enums import QuoteDirection

class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    TIMEOUT = "timeout"


class OrderExecutionRequest(BaseModel):
    direction: QuoteDirection
    pair: str = Field(
        ..., 
        pattern=r"^[a-zA-Z]+-[a-zA-Z]+$", 
        description="Asset pair in format 'USDT-USD'"
    )
    amount: Decimal
    incoming_account: str
    outgoing_account: str

class IProvider(Protocol):
    async def get_quote(
        self, 
        direction: QuoteDirection, 
        pair: str, 
        amount_in: Decimal | None = None, 
        amount_out: Decimal | None = None
    ) -> Any:
        ...

    async def execute(self, order: OrderExecutionRequest) -> dict: ...

class BaseProvider(ABC):
    @abstractmethod
    async def get_quote(
        self, 
        direction: QuoteDirection, 
        pair: str, 
        amount_in: Decimal | None = None, 
        amount_out: Decimal | None = None
    ) -> Any:
        pass

    @abstractmethod
    async def execute(self, order: OrderExecutionRequest) -> dict:
        pass
