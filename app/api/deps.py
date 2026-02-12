from typing import Annotated

import httpx
from fastapi import Depends, Request

from app.database.db_helper import db_helper
from app.database.uow import UnitOfWork
from app.services.liquidity import LiquidityService


async def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_uow() -> UnitOfWork:
    return UnitOfWork(db_helper.session_factory)


async def get_liquidity_service(
        uow: Annotated[UnitOfWork, Depends(get_uow)],
        http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> LiquidityService:
    return LiquidityService(uow, http_client)
