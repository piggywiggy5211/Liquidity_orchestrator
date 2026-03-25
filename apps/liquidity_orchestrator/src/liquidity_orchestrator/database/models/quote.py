from sqlalchemy import Column, DateTime, Enum, Integer, Numeric, String, Table

from liquidity_orchestrator.domain.enums import QuoteDirection

from .registry import metadata


quotes_table = Table(
    "quotes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("direction", Enum(QuoteDirection, native_enum=False), nullable=False),
    Column("pair", String, nullable=False),
    Column("amount_in", Numeric(precision=20, scale=8), nullable=False),
    Column("amount_out", Numeric(precision=20, scale=8), nullable=False),
    Column("fee_rate", Numeric(precision=20, scale=8), nullable=False),
    Column("provider_name", String, nullable=False),
    Column("valid_until", DateTime, nullable=False),
)
