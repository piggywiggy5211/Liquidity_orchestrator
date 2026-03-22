from entrypoints.fastapi.api.deps import get_liquidity_service, validate_amount
from entrypoints.fastapi.api.schemas.quote import QuoteRequest, QuoteResponse
from fastapi import APIRouter, Depends, Query
from service.dto import QuoteRequestDTO
from service.liquidity_service import LiquidityService


router = APIRouter(tags=["Quotes"])


@router.get("/calculate-quote", response_model=QuoteResponse)
async def calculate_quote(
    data: QuoteRequest = Query(),
    service: LiquidityService = Depends(get_liquidity_service),
):
    validate_amount(data.amount)

    dto = QuoteRequestDTO(
        direction=data.direction,
        pair=data.pair,
        amount=data.amount,
    )
    result = await service.get_quote(dto)

    return result
