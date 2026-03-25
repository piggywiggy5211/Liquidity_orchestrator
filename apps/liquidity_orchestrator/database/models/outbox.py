from domain.enums import OutboxEventType
from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, Table, func

from .registry import metadata


outbox_table = Table(
    "outbox",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id"), nullable=False),
    Column("event_type", Enum(OutboxEventType, native_enum=False), nullable=False),
    Column("payload", JSON, nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)
