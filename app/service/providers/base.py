import asyncio
import random
import uuid
from abc import ABC
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from functools import wraps
from typing import Any, Callable, Protocol

from cachetools import TTLCache, keys
from pydantic import BaseModel, Field

from app.core.config import settings
from app.domain.enums import QuoteDirection


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
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


def async_cachedmethod(get_cache: Callable):
    def dec(method):
        @wraps(method)
        async def memoized_async_method(self: BaseProvider, *args, **kwargs):
            cache = get_cache(self)
            key = keys.hashkey(self.__class__.__name__, *args, **kwargs)
            if key in cache:
                return cache[key]
            result = await method(self, *args, **kwargs)
            cache[key] = result
            return result

        return memoized_async_method

    return dec


class IProvider(Protocol):
    async def get_quote(
        self,
        direction: QuoteDirection,
        pair: str,
        amount_in: Decimal | None = None,
        amount_out: Decimal | None = None,
    ) -> dict[str, Any]: ...

    async def execute(self, order: OrderExecutionRequest) -> dict: ...


class BaseProvider(ABC):
    # Provider settings to be defined in subclasses
    fee_min: float
    fee_max: float
    latency_min: float
    latency_max: float
    timeout_prob: float
    fail_prob: float = 0.00003
    ref_prefix: str

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._cache = TTLCache(maxsize=1024, ttl=settings.quote_ttl)

    @async_cachedmethod(get_cache=lambda self: self._cache)
    async def get_quote(
        self,
        direction: QuoteDirection,
        pair: str,
        amount_in: Decimal | None = None,
        amount_out: Decimal | None = None,
    ) -> dict[str, Any]:
        fee_rate = Decimal(str(random.uniform(self.fee_min, self.fee_max)))

        if amount_in is not None:
            calc_amount_out = amount_in * (Decimal("1") - fee_rate)
            calc_amount_in = amount_in
        elif amount_out is not None:
            calc_amount_in = amount_out / (Decimal("1") - fee_rate)
            calc_amount_out = amount_out
        else:
            raise ValueError("Either amount_in or amount_out must be provided")

        valid_until = datetime.now() + timedelta(seconds=settings.quote_ttl)
        await asyncio.sleep(0)
        return {
            "pair": pair,
            "direction": direction,
            "amount_in": calc_amount_in,
            "amount_out": calc_amount_out,
            "fee_rate": fee_rate,
            "valid_until": valid_until,
        }

    async def execute(self, order: OrderExecutionRequest) -> dict:
        latency = random.uniform(self.latency_min, self.latency_max)
        await asyncio.sleep(latency)

        rand = random.random()
        if rand < self.fail_prob:
            status = ExecutionStatus.FAIL
        elif rand < self.fail_prob + self.timeout_prob:
            status = ExecutionStatus.TIMEOUT
        else:
            status = ExecutionStatus.SUCCESS

        return {
            "status": status,
            "provider_ref": f"ref-{self.ref_prefix}-{uuid.uuid4().hex[:8]}",
        }
