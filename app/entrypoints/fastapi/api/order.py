from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.entrypoints.fastapi.api.deps import get_liquidity_service, passes_idempotency_check, validate_amount
from app.entrypoints.fastapi.api.schemas.orders import OrderCreateRequest, OrderResponse
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
        raise HTTPException(
            status_code=400, detail="Idempotency check failed. Check X-Api-Ts header or duplicate request."
        )

    validate_amount(data.amount)

    dto = OrderCreateDTO(
        direction=data.direction,
        pair=data.pair,
        amount=data.amount,
        incoming_account=data.incoming_account,
        outgoing_account=data.outgoing_account,
    )
    result = await service.create_order(dto)

    background_tasks.add_task(service.uow.switch_session_context_for_task, service.execute_order, result.id)
    return result


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    service: LiquidityService = Depends(get_liquidity_service),
):
    """
    Retrieves information about a specific order by its unique ID.
    """
    result = await service.get_order(order_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return result
