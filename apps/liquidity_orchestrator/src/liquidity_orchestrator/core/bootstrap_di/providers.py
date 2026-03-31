from typing import AsyncGenerator, AsyncIterable, Mapping

import httpx
from dishka import Provider, Scope, provide
from lib.http_client import LoggingAsyncClient
from liquidity_orchestrator.core.config import Settings
from liquidity_orchestrator.database.db_helper import DatabaseHelper
from liquidity_orchestrator.database.uow import UnitOfWorkSqlAlchemy
from liquidity_orchestrator.domain.interfaces import IMetricsCollector, IProvider, IUnitOfWork
from liquidity_orchestrator.domain.metrics import InMemoryMetricsCollector
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
    @provide(scope=Scope.APP)
    async def httpx_client(self) -> AsyncGenerator[httpx.AsyncClient]:
        httpx_client = LoggingAsyncClient()
        yield httpx_client
        await httpx_client.aclose()

    @provide(scope=Scope.REQUEST)
    def get_uow(self, session_factory: async_sessionmaker[AsyncSession], session: AsyncSession) -> IUnitOfWork:
        return UnitOfWorkSqlAlchemy(session_factory, session)

    @provide(scope=Scope.APP)
    def get_metrics_collector(self) -> IMetricsCollector:
        return InMemoryMetricsCollector()

    @provide(scope=Scope.APP)
    def get_providers_map(
        self,
        httpx_client: httpx.AsyncClient,
        metrics_collector: IMetricsCollector,
    ) -> Mapping[str, type[IProvider]]:
        for p in PROVIDERS_MAP.values():
            p.httpx_client = httpx_client
            p.metrics_collector = metrics_collector
        return PROVIDERS_MAP

    @provide(scope=Scope.REQUEST)
    def get_service(
        self,
        uow: IUnitOfWork,
        providers_map: Mapping[str, type[IProvider]],
        metrics_collector: IMetricsCollector,
        settings: Settings,
    ) -> LiquidityService:
        return LiquidityService(
            uow=uow,
            providers_map=providers_map,
            service_fee=settings.service_fee,
            metrics=metrics_collector,
        )
