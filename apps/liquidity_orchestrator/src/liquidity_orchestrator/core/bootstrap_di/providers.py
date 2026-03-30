from typing import AsyncIterable

from dishka import Provider, Scope, provide
from liquidity_orchestrator.core.config import Settings
from liquidity_orchestrator.database.db_helper import DatabaseHelper
from liquidity_orchestrator.database.uow import UnitOfWorkSqlAlchemy
from liquidity_orchestrator.domain.interfaces import IProvider, IUnitOfWork
from liquidity_orchestrator.integrations.providers import PROVIDERS_MAP
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

    @provide
    def get_uow(self, session_factory: async_sessionmaker[AsyncSession], session: AsyncSession) -> IUnitOfWork:
        return UnitOfWorkSqlAlchemy(session_factory, session)

    service = provide(LiquidityService)

    @provide(scope=Scope.APP)
    def get_providers_map(self) -> dict[str, type[IProvider]]:
        return PROVIDERS_MAP
