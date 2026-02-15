from sqlalchemy import Table, Column, Integer, DateTime, JSON, ForeignKey, func, Enum
from .registry import metadata
from app.service.enums import OutboxEventType

outbox_table = Table(
    "outbox",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id"), nullable=False),
    Column("event_type", Enum(OutboxEventType, native_enum=False), nullable=False),
    Column("payload", JSON, nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)
