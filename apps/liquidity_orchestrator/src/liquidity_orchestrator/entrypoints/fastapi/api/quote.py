from fastapi import APIRouter, Depends, Query

from liquidity_orchestrator.entrypoints.fastapi.api.deps import get_liquidity_service, validate_amount
from liquidity_orchestrator.entrypoints.fastapi.api.schemas.quote import QuoteRequest, QuoteResponse
from liquidity_orchestrator.service.dto import QuoteRequestDTO
from liquidity_orchestrator.service.liquidity_service import LiquidityService


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
