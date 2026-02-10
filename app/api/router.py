from fastapi import APIRouter, Depends
from app.schemas.orders import OrderCreate, OrderResponse, QuoteRequest, QuoteResponse
from app.services.liquidity import LiquidityService
from app.core.database import db_helper
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from typing import Annotated

router = APIRouter()

# Global http client will be provided via dependency injection
# We'll use a helper to get the client from the app state
from fastapi import Request

async def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client

async def get_liquidity_service(
    db: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)]
) -> LiquidityService:
    return LiquidityService(db, http_client)

@router.post("/create_order", response_model=OrderResponse)
async def create_order(
    order_in: OrderCreate,
    service: Annotated[LiquidityService, Depends(get_liquidity_service)]
):
    return await service.create_order(order_in)

@router.get("/get_quote", response_model=QuoteResponse)
async def get_quote(
    quote_in: Annotated[QuoteRequest, Depends()],
    service: Annotated[LiquidityService, Depends(get_liquidity_service)]
):
    return await service.get_quote(quote_in)
