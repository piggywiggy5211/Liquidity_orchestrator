from typing import Annotated

import httpx
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_helper import db_helper
from app.database.uow import UnitOfWorkSqlAlchemy
from app.service.liquidity_service import LiquidityService


async def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


async def get_uow(session: AsyncSession = Depends(db_helper.session_getter)) -> UnitOfWorkSqlAlchemy:
    return UnitOfWorkSqlAlchemy(db_helper.session_factory, session)


async def get_liquidity_service(
        uow: Annotated[UnitOfWorkSqlAlchemy, Depends(get_uow)],
        http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> LiquidityService:
    return LiquidityService(uow, http_client)
