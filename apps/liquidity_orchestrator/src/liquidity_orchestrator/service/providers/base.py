import abc
from abc import ABC
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field

from liquidity_orchestrator.domain.enums import QuoteDirection


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


class IProvider(Protocol):
    name: str

    async def get_quote(  # TODO ADD DTO
        self,
        direction: QuoteDirection,
        pair: str,
        amount_out: Decimal,
    ) -> dict[str, Any]: ...

    async def execute(self, order: OrderExecutionRequest) -> dict: ...


class BaseProvider(ABC):
    name: str

    @abc.abstractmethod
    async def get_quote(  # TODO ADD DTO
        self,
        direction: QuoteDirection,
        pair: str,
        amount_out: Decimal,
    ) -> dict[str, Any]: ...

    @abc.abstractmethod
    async def execute(self, order: OrderExecutionRequest) -> dict: ...
