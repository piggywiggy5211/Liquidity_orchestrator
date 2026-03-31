from enum import StrEnum


class OrderStatus(StrEnum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class QuoteDirection(StrEnum):
    ON_RAMP = "on-ramp"
    OFF_RAMP = "off-ramp"


class OutboxEventType(StrEnum):
    ORDER_FALLBACK = "ORDER_FALLBACK"
    ORDER_COMPLETED = "ORDER_COMPLETED"
    ORDER_FAILED = "ORDER_FAILED"
