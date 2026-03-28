from typing import AsyncIterable

from dishka import Provider, Scope, provide
from liquidity_orchestrator.core.config import Settings
from liquidity_orchestrator.database.db_helper import DatabaseHelper
from liquidity_orchestrator.database.repositories.order import OrderRepository
from liquidity_orchestrator.database.repositories.outbox import OutboxRepository
from liquidity_orchestrator.database.repositories.quote import QuoteRepository
from liquidity_orchestrator.database.uow import UnitOfWorkSqlAlchemy
from liquidity_orchestrator.domain.interfaces import IRepository, IUnitOfWork
from liquidity_orchestrator.domain.models import Order, Outbox, Quote
from liquidity_orchestrator.service.liquidity_service import LiquidityService
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    def get_db_helper(self, settings: Settings) -> DatabaseHelper:
        return DatabaseHelper(
            url=str(settings.db.url),
            echo=settings.db.echo,
            echo_pool=settings.db.echo_pool,
            pool_size=settings.db.pool_size,
            max_overflow=settings.db.max_overflow,
            is_null_pool=settings.db.is_null_pool,
        )

    @provide(scope=Scope.APP)
    def get_engine(self, db_helper: DatabaseHelper) -> AsyncEngine:
        return db_helper.engine

    @provide(scope=Scope.APP)
    def get_session_factory(self, db_helper: DatabaseHelper) -> async_sessionmaker[AsyncSession]:
        return db_helper.session_factory

    @provide(scope=Scope.REQUEST)
    async def get_session(self, session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterable[AsyncSession]:
        async with session_factory() as session:
            yield session


class ServiceProvider(Provider):
    scope = Scope.REQUEST

    uow = provide(UnitOfWorkSqlAlchemy, provides=IUnitOfWork)
    service = provide(LiquidityService)

    @provide  # TODO FIX не должно быть своих сессий, возможно оставить один uow
    def get_order_repository(self, session: AsyncSession) -> IRepository[Order]:
        return OrderRepository(session)

    @provide
    def get_quote_repository(self, session: AsyncSession) -> IRepository[Quote]:
        return QuoteRepository(session)

    @provide
    def get_outbox_repository(self, session: AsyncSession) -> IRepository[Outbox]:
        return OutboxRepository(session)
