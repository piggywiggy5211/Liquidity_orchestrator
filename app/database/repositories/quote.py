from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Quote
from .base import BaseRepository


class QuoteRepository(BaseRepository[Quote]):
    def __init__(self, session: AsyncSession):
        super().__init__(Quote, session)
