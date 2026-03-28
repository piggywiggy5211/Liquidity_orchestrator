from fastapi import APIRouter

from liquidity_orchestrator.entrypoints.fastapi.api import order


api_router = APIRouter(prefix="")

api_router.include_router(order.router, prefix="/orders")
