from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.database.repositories.order import OrderRepository
from app.database.repositories.quote import QuoteRepository
from app.database.repositories.outbox import OutboxRepository



class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.session: AsyncSession | None = None

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def __aenter__(self):
        self.session = self.session_factory()
        self.orders = OrderRepository(self.session)
        self.quotes = QuoteRepository(self.session)
        self.outbox = OutboxRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.rollback()
        finally:
            await self.session.close()
            self.session = None
