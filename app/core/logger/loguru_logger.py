import json
import sys
from typing import TYPE_CHECKING

from loguru import logger
from loguru._better_exceptions import ExceptionFormatter

from app.core.config import settings
from app.core.logger.sanitizer import log_sanitizer

if TYPE_CHECKING:
    from loguru import Record

exception_formatter = ExceptionFormatter(
    colorize=False,
    encoding="utf-8",
    diagnose=settings.logging.debug,
    backtrace=settings.logging.debug,
    hidden_frames_filename=None,
    prefix="",
)


def serialize_json_log(record: "Record") -> str:
    log_record = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": record["level"].name,
        "service": "liquidity-orchestrator",
        "trace_id": record["extra"].get("trace_id", None),
        "span_id": record["extra"].get("span_id", None),
        "message": record["message"],
    }
    if record["exception"]:
        type_, value, tb = record["exception"]
        lines = exception_formatter.format_exception(type_, value, tb)  # type: ignore
        log_record.update({"exception": "".join(lines)})

    # Add extra data if any
    if record["extra"]:
        log_record.update(record["extra"])

    dirty_log = json.dumps(log_record, default=str, ensure_ascii=False)
    clear_log = log_sanitizer.sanitize(dirty_log)
    return f"{clear_log}\n"


def setup_loguru_logger():
    def json_sink(message):
        record = message.record
        serialized = serialize_json_log(record)
        sys.stdout.write(serialized)
        sys.stdout.flush()

    logger.remove()
    logger.add(
        sink=json_sink,
        level=settings.logging.log_level_value,
        diagnose=settings.logging.debug,
    )
