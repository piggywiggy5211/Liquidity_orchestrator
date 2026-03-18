from unittest.mock import AsyncMock, patch

import pytest

from app.api.deps import IDEMPOTENCY_SET


# Register DB fixtures from the separate module
pytest_plugins = ["tests.db_fixtures"]


@pytest.fixture(autouse=True)
def clear_idempotency_set():
    IDEMPOTENCY_SET.clear()
    yield


@pytest.fixture(autouse=True)
def mock_asyncio_sleep():
    with patch("asyncio.sleep", AsyncMock()):
        yield
