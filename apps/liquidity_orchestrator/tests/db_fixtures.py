import os
from enum import Enum
from typing import Generator

import pytest
import pytest_asyncio
from liquidity_orchestrator.core.config import settings
from liquidity_orchestrator.database.db_helper import DatabaseHelper, db_helper
from liquidity_orchestrator.database.models import map_models_sqlalchemy, metadata
from sqlalchemy.pool import NullPool
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


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db_helper(db_url):
    new_db_helper = DatabaseHelper(
        url=db_url,
        echo=settings.db.echo,
        echo_pool=settings.db.echo_pool,
        pool_size=settings.db.pool_size,
        max_overflow=settings.db.max_overflow,
        poolclass=NullPool,
    )
    db_helper.engine = new_db_helper.engine
    db_helper.session_factory = new_db_helper.session_factory
    yield
    await db_helper.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_db():
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    yield


@pytest.fixture
def session_factory():
    return db_helper.session_factory


@pytest_asyncio.fixture
async def db_session():
    async for session in db_helper.session_getter():
        yield session
