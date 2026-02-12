from typing import Annotated

import httpx
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db_helper
from app.services.liquidity import LiquidityService


async def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


async def get_liquidity_service(
        db: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> LiquidityService:
    return LiquidityService(db, http_client)
