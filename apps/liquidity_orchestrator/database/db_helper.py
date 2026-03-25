import typing
from typing import Any, AsyncGenerator, Type

from core.config import settings
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


if typing.TYPE_CHECKING:
    from sqlalchemy.pool.base import Pool


class DatabaseHelper:
    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        poolclass: Type["Pool"] | None = None,
    ) -> None:

        pool_settings: dict[str, Any] = {}
        if poolclass is NullPool:
            pool_settings["poolclass"] = poolclass
        else:
            pool_settings["pool_size"] = pool_size
            pool_settings["max_overflow"] = max_overflow

        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            **pool_settings,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        await self.engine.dispose()
        logger.info("Database engine disposed")

    async def session_getter(self) -> AsyncGenerator[AsyncSession]:
        async with self.session_factory() as session:
            yield session


db_helper = DatabaseHelper(
    url=str(settings.db.url),
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
)
