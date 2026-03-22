from domain.models import Outbox
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository


class OutboxRepository(BaseRepository[Outbox]):
    def __init__(self, session: AsyncSession):
        super().__init__(Outbox, session)
