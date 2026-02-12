from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Outbox
from .base import BaseRepository


class OutboxRepository(BaseRepository[Outbox]):
    def __init__(self, session: AsyncSession):
        super().__init__(Outbox, session)
