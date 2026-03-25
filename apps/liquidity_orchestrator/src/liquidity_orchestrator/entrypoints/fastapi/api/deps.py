import hashlib
from decimal import Decimal
from typing import Annotated
from urllib.parse import urlparse

import httpx
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from liquidity_orchestrator.core.config import settings
from liquidity_orchestrator.database.db_helper import db_helper
from liquidity_orchestrator.database.uow import UnitOfWorkSqlAlchemy
from liquidity_orchestrator.service.liquidity_service import LiquidityService


async def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


IDEMPOTENCY_SET = set()


async def passes_idempotency_check(
    request: Request,
    x_api_ts: Annotated[str | None, Header(alias="X-Api-Ts")] = None,
) -> bool:
    if x_api_ts is None:
        return False

    method = request.method
    parsed = urlparse(str(request.url))
    path_and_query = parsed._replace(scheme="", netloc="").geturl()
    body = (await request.body()).decode("utf-8")
    data_to_sign = f"{x_api_ts}{method}{path_and_query}{body}"
    h = hashlib.sha256(data_to_sign.encode("utf-8")).hexdigest()

    if h in IDEMPOTENCY_SET:
        return False
    IDEMPOTENCY_SET.add(h)
    return True


async def get_uow(session: AsyncSession = Depends(db_helper.session_getter)) -> UnitOfWorkSqlAlchemy:
    return UnitOfWorkSqlAlchemy(db_helper.session_factory, session)


async def get_liquidity_service(
    uow: Annotated[UnitOfWorkSqlAlchemy, Depends(get_uow)],
    http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> LiquidityService:
    return LiquidityService(uow, http_client)


def validate_amount(amount: Decimal):
    if amount > settings.max_order_amount:
        raise HTTPException(status_code=422, detail="Not allowed, amount over the limit")
