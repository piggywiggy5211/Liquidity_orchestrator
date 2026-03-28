import os
from enum import Enum
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from dishka import AsyncContainer
from liquidity_orchestrator.core.bootstrap_di.container import bootstrap_container
from liquidity_orchestrator.core.config import Settings
from liquidity_orchestrator.database.models import map_models_sqlalchemy, metadata
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer


type DB_URL = str


class TestDBType(str, Enum):
    LOCAL = "LOCAL"
    TESTCONTAINER = "TESTCONTAINER"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_map_models():
    map_models_sqlalchemy()


@pytest.fixture(scope="session")
def test_db_type() -> TestDBType:
    value = os.getenv("TEST_DB_TYPE", TestDBType.TESTCONTAINER.value)
    return TestDBType(value)


@pytest.fixture(scope="session")
def db_url(test_db_type) -> Generator[DB_URL, None]:
    if test_db_type == TestDBType.TESTCONTAINER:
        with PostgresContainer("postgres:18") as postgres:
            url = postgres.get_connection_url()
            if "://" in url:
                _, rest = url.split("://", 1)
                url = f"postgresql+asyncpg://{rest}"
            yield url
    else:  # Local DB from docker-compose.yml
        yield "postgresql+asyncpg://orchestrator:orchestrator_pass@localhost:5432/liquidity_orchestrator"


@pytest_asyncio.fixture(scope="session")
async def dishka_container(db_url) -> AsyncGenerator[AsyncContainer, None]:
    test_settings = Settings()
    test_settings.db.url = db_url
    test_settings.db.echo = False
    test_settings.db.is_null_pool = True

    container = bootstrap_container(test_settings)
    yield container
    await container.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_db(dishka_container: AsyncContainer):
    engine = await dishka_container.get(AsyncEngine)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    yield


@pytest.fixture
async def session_factory(dishka_container: AsyncContainer):
    return await dishka_container.get(async_sessionmaker[AsyncSession])


@pytest_asyncio.fixture
async def db_session(dishka_container: AsyncContainer):
    async with dishka_container() as request_container:
        yield await request_container.get(AsyncSession)
