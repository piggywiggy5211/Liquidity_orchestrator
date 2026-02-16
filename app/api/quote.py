from fastapi import APIRouter, Depends, Query, HTTPException

from app.api.deps import get_liquidity_service
from app.api.schemas.quote import QuoteRequest, QuoteResponse
from app.service.dto import QuoteGetDTO
from app.service.liquidity_service import LiquidityService

router = APIRouter(tags=["Quotes"])

@router.get("/calculate-quote", response_model=QuoteResponse)
async def calculate_quote(
        data: QuoteRequest = Query(),
        service: LiquidityService = Depends(get_liquidity_service),
):
    if not service.validate_sum(data.amount):
        raise HTTPException(status_code=422, detail="Not allowed, amount over the limit")

    dto = QuoteGetDTO(
        direction=data.direction,
        pair=data.pair,
        amount=data.amount,
    )
    result = await service.get_quote(dto)
    
    return result