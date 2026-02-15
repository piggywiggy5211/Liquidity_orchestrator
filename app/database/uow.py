import contextvars
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.database.repositories.order import OrderRepository
from app.database.repositories.quote import QuoteRepository
from app.database.repositories.outbox import OutboxRepository


class UnitOfWorkSqlAlchemy:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], session: AsyncSession):
        self.session_factory = session_factory
        self.ctx_session = contextvars.ContextVar("current_session", default=session)

    @property
    def session(self) -> AsyncSession:
        return self.ctx_session.get()

    @property
    def orders(self) -> OrderRepository:
        return OrderRepository(self.session)

    @property
    def quotes(self) -> QuoteRepository:
        return QuoteRepository(self.session)

    @property
    def outbox(self) -> OutboxRepository:
        return OutboxRepository(self.session)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rollback()
