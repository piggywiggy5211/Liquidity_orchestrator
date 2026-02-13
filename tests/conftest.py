import pathlib
import sys

import pytest

# Ensure project root on sys.path for imports like `import main`
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.models import map_models_sqlalchemy, metadata
from app.database.db_helper import db_helper

@pytest.fixture
def setup_db_mappings():
    map_models_sqlalchemy()
    yield

@pytest.fixture
def session_factory(setup_db_mappings):
    return db_helper.session_factory

@pytest.fixture
async def clean_db():
    async with db_helper.engine.begin() as conn:
        for table in reversed(metadata.sorted_tables):
            await conn.execute(table.delete())
