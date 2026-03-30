from typing import Any, Callable, Optional, Protocol, Sequence

from liquidity_orchestrator.domain.enums import ProviderExecutionStatus

from .models import Order, Outbox, Quote
from .provider_dto import (
    ProviderExecutionResponse,
    ProviderGetQuoteRequest,
    ProviderOrderExecutionRequest,
    ProviderQuoteResponse,
)


class IRepository[ModelType](Protocol):
    async def get(self, record_id: int) -> Optional[ModelType]: ...

    async def get_all(self) -> Sequence[ModelType]: ...

    def add(self, instance: ModelType) -> None: ...

    async def update(self, record_id: int, **kwargs: Any) -> None: ...

    async def delete(self, instance: ModelType) -> None: ...


class IUnitOfWork(Protocol):
    @property
    def orders(self) -> IRepository[Order]: ...
    @property
    def quotes(self) -> IRepository[Quote]: ...
    @property
    def outbox(self) -> IRepository[Outbox]: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def switch_session_context_for_task(self, func: Callable, *args: Any, **kwargs: Any) -> Any: ...

    async def __aenter__(self) -> "IUnitOfWork": ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...


class IProvider(Protocol):
    name: str

    async def get_quote(self, request: ProviderGetQuoteRequest) -> ProviderQuoteResponse: ...

    async def execute(self, order: ProviderOrderExecutionRequest) -> ProviderExecutionResponse: ...


class IMetricsCollector(Protocol):
    def record_execution(self, provider_name: str, latency: float, status: ProviderExecutionStatus) -> None: ...

    @property
    def average_latency(self) -> dict[str, float]: ...

    @property
    def timeout_percentage(self) -> dict[str, float]: ...
