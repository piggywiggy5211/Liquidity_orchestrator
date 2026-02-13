from fastapi import APIRouter, Depends, Query

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
    dto = QuoteGetDTO(
        direction=data.direction,
        pair=data.pair,
        amount=data.amount,
    )
    result = await service.get_quote(dto)
    
    return QuoteResponse(
        incoming_amount=f"{result.incoming_amount:.2f}",
        incoming_asset_code=result.incoming_asset_code,
        outgoing_amount=f"{result.outgoing_amount:.2f}",
        outgoing_asset_code=result.outgoing_asset_code,
        fee_amount=f"{result.fee_amount:.2f}",
        fee_asset_code=result.fee_asset_code,
    )
