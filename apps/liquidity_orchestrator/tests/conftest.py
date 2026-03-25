from unittest.mock import AsyncMock, patch

import pytest
from entrypoints.fastapi.api.deps import IDEMPOTENCY_SET
from entrypoints.fastapi.main import main_app
from starlette.testclient import TestClient


pytest_plugins = ["tests.db_fixtures"]


@pytest.fixture()
def clear_idempotency_set():
    IDEMPOTENCY_SET.clear()
    yield


@pytest.fixture()
def mock_asyncio_sleep():
    with patch("asyncio.sleep", AsyncMock()):
        yield


@pytest.fixture(scope="session")
def client():
    with TestClient(main_app) as c:
        yield c
