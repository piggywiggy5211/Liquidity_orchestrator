import logging

import pytest
from lib.logger.logger import setup_logger
from loguru import logger


@pytest.fixture
def configure_logging():
    # Setup logger to output JSON to sys.stdout so capsys can capture it
    setup_logger(log_level="INFO", debug=False)
    yield
    # Reset loguru after each test
    logger.remove()
    # Reset standard logging handlers after each test
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
