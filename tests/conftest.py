import pathlib
import sys

import pytest
import pytest_asyncio

# Ensure project root on sys.path for imports like `import main`
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.models import map_models_sqlalchemy, metadata
from app.database.db_helper import db_helper

from unittest.mock import AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_asyncio_sleep():
    with patch("asyncio.sleep", AsyncMock()):
        yield

@pytest.fixture
def setup_db_mappings():
    map_models_sqlalchemy()
    yield

@pytest.fixture
def session_factory(setup_db_mappings):
    return db_helper.session_factory

@pytest_asyncio.fixture
async def db_session(setup_db_mappings):
    async for session in db_helper.session_getter():
        yield session


@pytest.fixture
async def clean_db():
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
