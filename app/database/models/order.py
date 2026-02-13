from sqlalchemy import Table, Column, Integer, String, DateTime, func, Enum
from .registry import metadata
from app.service.enums import OrderStatus

orders_table = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("quote_id", String, unique=True, nullable=True),
    Column(
        "status", 
        Enum(OrderStatus, native_enum=False), 
        default=OrderStatus.NEW,
        server_default=OrderStatus.NEW.value,
        nullable=False
    ),
    Column("provider_name", String, nullable=True),
    Column("provider_ref", String, nullable=True),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now(), nullable=False),
)
