import json
from unittest.mock import MagicMock

from app.core.logger.loguru_logger import serialize_json_log


def test_json_logging_format():
    record = {
        "time": MagicMock(),
        "level": MagicMock(name="INFO"),
        "message": "test message with IBAN DE12345678901234567890",
        "extra": {"trace_id": "1234567890", "span_id": "0987654321"},
        "exception": None,
    }
    record["time"].strftime.return_value = "2026-02-10T14:30:15.123Z"
    record["level"].name = "INFO"

    log_json = serialize_json_log(record)
    data = json.loads(log_json)

    assert data["service"] == "liquidity-orchestrator"
    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert "DE12****7890" in data["message"]
    assert "trace_id" in data
