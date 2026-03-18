from sqlalchemy import Column, DateTime, Enum, Integer, Numeric, String, Table, func

from app.domain.enums import OrderStatus, QuoteDirection

from .registry import metadata


orders_table = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("incoming_amount", Numeric(precision=20, scale=8), nullable=False),
    Column("outgoing_amount", Numeric(precision=20, scale=8), nullable=False),
    Column("incoming_account", String, nullable=False),
    Column("outgoing_account", String, nullable=False),
    Column("direction", Enum(QuoteDirection, native_enum=False), nullable=False),
    Column("pair", String, nullable=False),
    Column("quote_id", String, unique=True, nullable=True),
    Column(
        "status",
        Enum(OrderStatus, native_enum=False),
        default=OrderStatus.NEW,
        server_default=OrderStatus.NEW.value,
        nullable=False,
    ),
    Column("provider_ref", String, nullable=True),
    Column("version", Integer, server_default="0", nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now(), nullable=False),
)
