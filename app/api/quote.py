from fastapi import APIRouter, Depends, Query

from app.api.deps import get_liquidity_service
from app.api.schemas.quote import QuoteRequest, QuoteResponse
from app.service.liquidity_service import LiquidityService

router = APIRouter()

@router.get("/get_quote", response_model=QuoteResponse)
async def get_quote(
        quote_in: QuoteRequest = Query(),
        service: LiquidityService = Depends(get_liquidity_service),
):
    return await service.get_quote(quote_in)
