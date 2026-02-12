from datetime import datetime
from sqlalchemy import String, DateTime, JSON, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from .enums import OutboxEventType


class Outbox(Base):
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    event_type: Mapped[OutboxEventType] = mapped_column(Enum(OutboxEventType, native_enum=False))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(), 
        server_default=func.now()
    )
