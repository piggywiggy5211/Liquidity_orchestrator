
import httpx
from loguru import logger

from app.schemas.orders import OrderCreate, OrderResponse, QuoteRequest, QuoteResponse
from app.service.interfaces import IUnitOfWork


class LiquidityService:
    def __init__(self, uow: IUnitOfWork, http_client: httpx.AsyncClient):
        self.uow = uow
        self.http_client = http_client

    async def create_order(self, order_in: OrderCreate) -> OrderResponse:
        logger.info(f"Creating order for amount {order_in.amount}")
        async with self.uow:
            # Здесь будет логика создания заказа через репозитории
            # order = await self.uow.orders.create(...)
            # await self.uow.commit()
            response = await self.http_client.get("https://pokeapi.co/api/v2/pokemon/ditto")
        
        return OrderResponse(id="ord_12345", status="pending")

    async def get_quote(self, quote_in: QuoteRequest) -> QuoteResponse:
        logger.info(f"Getting quote for {quote_in.from_currency} -> {quote_in.to_currency}")
        # Stub logic
        return QuoteResponse(
            quote_id="qt_67890",
            rate=0.95,
            estimated_amount=quote_in.amount * 0.95
        )
