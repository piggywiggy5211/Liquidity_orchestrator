from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.api.deps import get_liquidity_service, passes_idempotency_check
from app.api.schemas.orders import OrderCreateRequest, OrderResponse
from app.service.dto import OrderCreateDTO
from app.service.liquidity_service import LiquidityService

router = APIRouter(tags=["Orders"])


@router.post("", response_model=OrderResponse)
async def create_order(
        data: OrderCreateRequest,
        background_tasks: BackgroundTasks,
        idempotency_passed: bool = Depends(passes_idempotency_check),
        service: LiquidityService = Depends(get_liquidity_service),
):
    if not idempotency_passed:
        raise HTTPException(status_code=400, detail="Idempotency check failed. Check X-Api-Ts header or duplicate request.")

    if not service.validate_sum(data.amount):
        raise HTTPException(status_code=422, detail="Not allowed, amount over the limit")

    dto = OrderCreateDTO(
        direction=data.direction,
        pair=data.pair,
        amount=data.amount,
        incoming_account=data.incoming_account,
        outgoing_account=data.outgoing_account,
    )
    result = await service.create_order(dto)

    background_tasks.add_task(service.task_wrapper, service.execute_order, result.id)
    return OrderResponse(**result.model_dump())
