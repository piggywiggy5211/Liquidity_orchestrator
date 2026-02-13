from sqlalchemy import Table, Column, Integer, String, DateTime, Numeric, Enum
from .registry import metadata
from app.service.enums import QuoteDirection

quotes_table = Table(
    "quotes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("direction", Enum(QuoteDirection, native_enum=False), nullable=False),
    Column("pair", String, nullable=False),
    Column("amount_in", Numeric(precision=20, scale=8), nullable=False),
    Column("amount_out", Numeric(precision=20, scale=8), nullable=False),
    Column("amount_fee", Numeric(precision=20, scale=8), nullable=False),
    Column("provider_name", String, nullable=False),
    Column("valid_until", DateTime, nullable=False),
)
