from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_liquidity_service
from app.schemas.orders import OrderCreate, OrderResponse, QuoteRequest, QuoteResponse
from app.services.liquidity import LiquidityService

router = APIRouter()

@router.get("/get_quote", response_model=QuoteResponse)
async def get_quote(
        quote_in: Annotated[QuoteRequest, Depends()],
        service: Annotated[LiquidityService, Depends(get_liquidity_service)],
):
    return await service.get_quote(quote_in)
