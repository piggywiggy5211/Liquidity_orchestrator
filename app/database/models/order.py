from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from .enums import OrderStatus


class Order(Base):
    quote_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False), 
        default=OrderStatus.NEW,
        server_default=OrderStatus.NEW.value
    )
    provider_name: Mapped[str] = mapped_column(String)
    provider_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now()
    )
