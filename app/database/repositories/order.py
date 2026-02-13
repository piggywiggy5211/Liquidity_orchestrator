from datetime import datetime
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.service.models import Order
from .base import BaseRepository
from ...service.dto import OrderExecutionResult, OrderDTO


class OrderRepository(BaseRepository[Order, OrderDTO]):
    def __init__(self, session: AsyncSession):
        super().__init__(Order, OrderDTO, session)

    async def set_execution_result(self, data: OrderExecutionResult) -> None:
        update_values = {
            "status": data.status,
            "updated_at": datetime.now(),
        }
        if data.quote_id:
            update_values["quote_id"] = data.quote_id
        if data.provider_ref:
            update_values["provider_ref"] = data.provider_ref


        stmt = (
            update(self.model)
            .where(self.model.id == data.order_id)
            .values(**update_values)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
