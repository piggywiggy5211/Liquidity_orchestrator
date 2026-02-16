from contextvars import ContextVar
from typing import Protocol, Optional, Sequence, Callable, AsyncContextManager

from app.service.dto import OrderExecutionResult, OrderDTO, QuoteDTO, OutboxDTO
from app.service.models import Order, Quote, Outbox


class IRepository[M, D](Protocol):
    async def get(self, id: int) -> tuple[Optional[M], Optional[D]]: ...

    async def get_all(self) -> tuple[Sequence[M], Sequence[D]]: ...

    def add(self, instance: M) -> None: ...

    async def delete(self, instance: M) -> None: ...


class IRepositoryOrder(IRepository[Order, OrderDTO]):
    async def set_execution_result(self, data: OrderExecutionResult) -> None: ...


class IUnitOfWork(Protocol):
    session_factory: Callable[[], AsyncContextManager]
    ctx_session: ContextVar

    orders: IRepositoryOrder
    quotes: IRepository[Quote, QuoteDTO]
    outbox: IRepository[Outbox, OutboxDTO]

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def __aenter__(self) -> "IUnitOfWork": ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...
