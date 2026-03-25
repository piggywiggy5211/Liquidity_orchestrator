import json
import sys
from typing import TYPE_CHECKING

from lib.sanitizers.log_sanitizer import log_sanitizer
from loguru import logger
from loguru._better_exceptions import ExceptionFormatter


if TYPE_CHECKING:
    from loguru import Record


def serialize_json_log(record: "Record", exception_formatter: ExceptionFormatter) -> str:
    log_record = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": record["level"].name,
        "service": "liquidity-orchestrator",
        "message": record["message"],
    }
    trace_id = record["extra"].pop("trace_id", None)
    span_id = record["extra"].pop("span_id", None)
    if trace_id or span_id:
        log_record.update({"trace_id": trace_id, "span_id": span_id})

    if record["exception"]:
        type_, value, tb = record["exception"]
        lines = exception_formatter.format_exception(type_, value, tb)  # type: ignore
        log_record.update({"exception": "".join(lines)})

    if record["extra"]:
        log_record.update(record["extra"])

    dirty_log = json.dumps(log_record, default=str, ensure_ascii=False)
    clear_log = log_sanitizer.sanitize(dirty_log)
    return f"{clear_log}\n"


def setup_loguru_logger(log_level_value: str, debug: bool):
    exception_formatter = ExceptionFormatter(
        colorize=False,
        encoding="utf-8",
        diagnose=debug,
        backtrace=debug,
        hidden_frames_filename=None,
        prefix="",
    )

    def json_sink(message):
        record = message.record
        serialized = serialize_json_log(record, exception_formatter)
        sys.stdout.write(serialized)
        sys.stdout.flush()

    logger.remove()
    logger.add(
        sink=json_sink,
        level=log_level_value,
        diagnose=debug,
    )
