
import httpx
from datetime import datetime
from decimal import Decimal
from loguru import logger

from app.core.config import settings
from app.service.enums import OrderStatus
from app.service.models import Order
from app.service.dto import (
    QuoteGetDTO, 
    QuoteResultDTO,
    OrderCreateDTO,
    OrderResultDTO,
)
from app.service.interfaces import IUnitOfWork


class LiquidityService:
    def __init__(self, uow: IUnitOfWork, http_client: httpx.AsyncClient):
        self.uow = uow
        self.http_client = http_client

    async def create_order(self, data: OrderCreateDTO) -> OrderResultDTO:
        logger.info(f"Creating order for amount {data.amount} pair {data.pair}")
        
        async with self.uow:
            order = Order(
                amount=data.amount,
                direction=data.direction,
                pair=data.pair,
                incoming_account=data.incoming_account,
                outgoing_account=data.outgoing_account,
                status=OrderStatus.NEW,
                created_at=datetime.now()
            )
            self.uow.orders.add(order)
            await self.uow.commit()
            
        return OrderResultDTO(
            id=str(order.id),
            status=order.status.value,
            direction=order.direction,
            pair=order.pair,
            incoming_amount=order.amount,
            incoming_account=order.incoming_account,
            outgoing_amount=Decimal("0"), # Пока заглушка для расчетов
            outgoing_account=order.outgoing_account,
            commission_amount=Decimal("0"), # Пока заглушка для расчетов
            created_at=order.created_at
        )

    async def get_quote(self, data: QuoteGetDTO) -> QuoteResultDTO:
        logger.info(f"calculating quote for pair={data.pair} direction={data.direction}, amount={data.amount}")
        incoming_asset, outgoing_asset, *_ = data.pair.split("-")
        fee_amount = data.amount * settings.service_fee
        outgoing_amount = data.amount - fee_amount

        return QuoteResultDTO(
            incoming_amount=data.amount,
            incoming_asset_code=incoming_asset,
            outgoing_amount=outgoing_amount,
            outgoing_asset_code=outgoing_asset,
            fee_amount=fee_amount,
            fee_asset_code=incoming_asset,
        )
