from decimal import Decimal

from entrypoints.fastapi.schemas import ExecuteResponse, ExecutionStatus, OrderExecutionRequest, QuoteResponse
from fastapi import APIRouter, HTTPException, Path, Query, status
from service.cache import CACHES, async_cachedmethod
from service.enums import QuoteDirection
from service.logic import execute_order, generate_quote
from service.providers import configs


router = APIRouter()


@router.get("/provider_{provider_id}/quote", response_model=QuoteResponse)
@async_cachedmethod(lambda: CACHES)
async def provider_quote(
    direction: QuoteDirection,
    pair: str,
    provider_id: str = Path(..., description="Provider ID (e.g. a, b, c)"),
    amount_out: Decimal = Query(...),
):
    if provider_id not in configs:
        raise HTTPException(status_code=404, detail="Provider not found")
    return generate_quote(configs[provider_id], direction, pair, amount_out)


@router.post("/provider_{provider_id}/execute", response_model=ExecuteResponse)
async def provider_execute(
    request: OrderExecutionRequest,
    provider_id: str = Path(..., description="provider ID (e.g. a, b, c)"),
):
    if provider_id not in configs:
        raise HTTPException(status_code=404, detail="Provider not found")

    response = await execute_order(configs[provider_id], request)
    if response.status == ExecutionStatus.TIMEOUT:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Provider timeout")

    return response
