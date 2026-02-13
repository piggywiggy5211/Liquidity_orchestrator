
import httpx
from decimal import Decimal
from loguru import logger

from app.api.schemas.order import OrderCreateRequest, OrderResponse
from app.core.config import settings
from app.service.dto import QuoteGetDTO, QuoteResultDTO
from app.service.interfaces import IUnitOfWork


class LiquidityService:
    def __init__(self, uow: IUnitOfWork, http_client: httpx.AsyncClient):
        self.uow = uow
        self.http_client = http_client

    async def create_order(self, order_in: OrderCreateRequest) -> OrderResponse:
        logger.info(f"Creating order for amount {order_in.amount}")
        async with self.uow:
            # Здесь будет логика создания заказа через репозитории
            # order = await self.uow.orders.create(...)
            # await self.uow.commit()
            response = await self.http_client.get("https://pokeapi.co/api/v2/pokemon/ditto")
        
        return OrderResponse(id="ord_12345", status="pending")

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
