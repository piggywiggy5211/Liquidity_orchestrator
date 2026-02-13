from sqlalchemy.ext.asyncio import AsyncSession
from app.service.models import Outbox
from app.service.dto import OutboxDTO
from .base import BaseRepository


class OutboxRepository(BaseRepository[Outbox, OutboxDTO]):
    def __init__(self, session: AsyncSession):
        super().__init__(Outbox, OutboxDTO, session)
