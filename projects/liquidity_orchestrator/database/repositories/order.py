from domain.models import Order
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession):
        super().__init__(Order, session)
