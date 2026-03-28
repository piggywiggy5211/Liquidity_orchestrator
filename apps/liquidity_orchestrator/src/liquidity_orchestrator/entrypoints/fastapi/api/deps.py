import hashlib
from decimal import Decimal
from typing import Annotated
from urllib.parse import urlparse

from fastapi import Header, HTTPException, Request

from liquidity_orchestrator.core.config import settings


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


def validate_amount(amount: Decimal):
    if amount > settings.max_order_amount:
        raise HTTPException(status_code=422, detail="Not allowed, amount over the limit")
