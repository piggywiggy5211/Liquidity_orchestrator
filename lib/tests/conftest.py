import pytest
from lib.logger.logger import setup_logger

@pytest.fixture(autouse=True)
def configure_logging():
    # Setup logger to output JSON to sys.stdout so capsys can capture it
    setup_logger(log_level="INFO", debug=False)
