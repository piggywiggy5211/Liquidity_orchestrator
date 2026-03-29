import contextvars
from typing import Any, Callable

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from liquidity_orchestrator.database.repositories.order import OrderRepository
from liquidity_orchestrator.database.repositories.outbox import OutboxRepository
from liquidity_orchestrator.database.repositories.quote import QuoteRepository


class UnitOfWorkSqlAlchemy:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], session: AsyncSession):
        self.session_factory = session_factory
        self.ctx_session = contextvars.ContextVar("current_session", default=session)

    @property
    def _session(self) -> AsyncSession:
        return self.ctx_session.get()

    @property
    def orders(self) -> OrderRepository:
        return OrderRepository(self._session)

    @property
    def quotes(self) -> QuoteRepository:
        return QuoteRepository(self._session)

    @property
    def outbox(self) -> OutboxRepository:
        return OutboxRepository(self._session)

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except StaleDataError:
            logger.error("it was updated by another process")
            raise

    async def rollback(self) -> None:
        await self._session.rollback()

    async def switch_session_context_for_task(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        async with self.session_factory() as session:
            token = self.ctx_session.set(session)
            try:
                return await func(*args, **kwargs)
            finally:
                self.ctx_session.reset(token)

    async def __aenter__(self) -> "UnitOfWorkSqlAlchemy":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.rollback()
