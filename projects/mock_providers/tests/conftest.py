from unittest.mock import AsyncMock, patch

import pytest
from mock_providers.main import app
from starlette.testclient import TestClient


@pytest.fixture()
def mock_asyncio_sleep():
    with patch("asyncio.sleep", AsyncMock()):
        yield


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
