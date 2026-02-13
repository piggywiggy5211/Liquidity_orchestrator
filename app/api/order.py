from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_liquidity_service
from app.api.schemas.orders import OrderCreateRequest, OrderResponse
from app.service.liquidity_service import LiquidityService
from app.service.dto import OrderCreateDTO

router = APIRouter(tags=["Orders"])


@router.post("", response_model=OrderResponse)
async def create_order(
        data: OrderCreateRequest,
        service: Annotated[LiquidityService, Depends(get_liquidity_service)],
):
    dto = OrderCreateDTO(
        direction=data.direction,
        pair=data.pair,
        amount=data.amount,
        incoming_account=data.incoming_account,
        outgoing_account=data.outgoing_account,
    )
    result = await service.create_order(dto)
    return OrderResponse(
        id=result.id,
        status=result.status,
        direction=result.direction,
        pair=result.pair,
        incoming_amount=result.incoming_amount,
        incoming_account=result.incoming_account,
        outgoing_amount=result.outgoing_amount,
        outgoing_account=result.outgoing_account,
        commission_amount=result.commission_amount,
        created_at=result.created_at,
    )
