from enum import Enum


class OrderStatus(str, Enum):
    NEW = "NEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class QuoteDirection(str, Enum):
    ON_RAMP = "on-ramp"
    OFF_RAMP = "off-ramp"


class OutboxEventType(str, Enum):
    ORDER_FALLBACK = "ORDER_FALLBACK"
    ORDER_COMPLETED = "ORDER_COMPLETED"
    ORDER_FAILED = "ORDER_FAILED"
