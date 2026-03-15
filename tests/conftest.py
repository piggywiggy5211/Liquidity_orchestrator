import pathlib
import sys
from unittest.mock import AsyncMock, patch

import pytest


# Ensure the project root on sys.path for imports like `import main`
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
