from fastapi import APIRouter

from app.api import order, quote

api_router = APIRouter(prefix="")

api_router.include_router(order.router, prefix="/orders")
api_router.include_router(quote.router, prefix="/orders")
