from typing import Protocol
from app.database.repositories.order import OrderRepository
from app.database.repositories.quote import QuoteRepository
from app.database.repositories.outbox import OutboxRepository


class IUnitOfWork(Protocol):
    orders: OrderRepository
    quotes: QuoteRepository
    outbox: OutboxRepository

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...

    async def __aenter__(self) -> "IUnitOfWork":
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...
