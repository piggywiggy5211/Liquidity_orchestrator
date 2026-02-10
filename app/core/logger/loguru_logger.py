import json
import re
import sys
from typing import TYPE_CHECKING

from loguru import logger
from loguru._better_exceptions import ExceptionFormatter
from opentelemetry import trace

from app.core.config import settings

if TYPE_CHECKING:
    from loguru import Record

IBAN_REGEX = re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,27}\b')  # iban length  range 15 - 31


def mask_iban(text: str) -> str:
    def replace(match):
        iban = match.group(0)
        return f"{iban[:4]}****{iban[-4:]}"

    return IBAN_REGEX.sub(replace, text)


exception_formatter = ExceptionFormatter(
    colorize=False,
    encoding="utf-8",
    diagnose=settings.logging.debug,
    backtrace=settings.logging.debug,
    hidden_frames_filename=None,
    prefix="",
)


def serialize_json_log(record: "Record") -> str:
    # Get trace context
    span = trace.get_current_span()
    span_context = span.get_span_context()

    trace_id = format(span_context.trace_id, "032x") if span_context.is_valid else "0" * 32
    span_id = format(span_context.span_id, "016x") if span_context.is_valid else "0" * 16

    message = record["message"]
    # Apply sanitizer
    message = mask_iban(message)

    log_record = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": record["level"].name,
        "service": "liquidity-orchestrator",
        "trace_id": trace_id,
        "span_id": span_id,
        "message": message,
    }
    if record["exception"]:
        type_, value, tb = record["exception"]
        lines = exception_formatter.format_exception(type_, value, tb)  # type: ignore
        log_record.update({"exception": "".join(lines)})

    # Add extra data if any
    if record["extra"]:
        log_record.update(record["extra"])

    # return json.dumps(log_record, default=str) + "\n"
    return json.dumps(log_record, default=str, ensure_ascii=False) + "\n"


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
