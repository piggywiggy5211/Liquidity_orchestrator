from fastapi import APIRouter

from liquidity_orchestrator.entrypoints.fastapi.api import order, quote


api_router = APIRouter(prefix="")

api_router.include_router(quote.router, prefix="")
api_router.include_router(order.router, prefix="/orders")
