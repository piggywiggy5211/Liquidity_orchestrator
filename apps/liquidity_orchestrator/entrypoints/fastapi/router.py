from entrypoints.fastapi.api import order, quote
from fastapi import APIRouter


api_router = APIRouter(prefix="")

api_router.include_router(quote.router, prefix="")
api_router.include_router(order.router, prefix="/orders")
