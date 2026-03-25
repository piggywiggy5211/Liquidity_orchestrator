from liquidity_orchestrator.domain.models import Quote
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository


class QuoteRepository(BaseRepository[Quote]):
    def __init__(self, session: AsyncSession):
        super().__init__(Quote, session)
