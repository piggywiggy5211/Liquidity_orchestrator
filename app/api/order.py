from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_liquidity_service
from app.api.schemas.order import OrderCreateRequest, OrderResponse
from app.service.liquidity_service import LiquidityService

router = APIRouter(tags=["Orders"])


@router.post("/create_order", response_model=OrderResponse)
async def create_order(
        order_in: OrderCreateRequest,
        service: LiquidityService = Depends(get_liquidity_service),
):
    return await service.create_order(order_in)
