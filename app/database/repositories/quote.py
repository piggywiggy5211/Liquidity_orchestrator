from sqlalchemy.ext.asyncio import AsyncSession
from app.service.models import Quote
from app.service.dto import QuoteDTO
from .base import BaseRepository


class QuoteRepository(BaseRepository[Quote, QuoteDTO]):
    def __init__(self, session: AsyncSession):
        super().__init__(Quote, QuoteDTO, session)
