from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Enum
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from decimal import Decimal
from .enums import QuoteDirection


class Quote(Base):
    direction: Mapped[QuoteDirection] = mapped_column(Enum(QuoteDirection, native_enum=False))
    pair: Mapped[str] = mapped_column(String)  # e.g., "usd-usdt"
    amount_in: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8))
    amount_out: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8))
    amount_fee: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=8))
    provider_name: Mapped[str] = mapped_column(String)
    valid_until: Mapped[datetime] = mapped_column(DateTime)
