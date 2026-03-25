import asyncio
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from mock_providers.core.config import settings
from mock_providers.entrypoints.fastapi.schemas import (
    ExecuteResponse,
    ExecutionStatus,
    OrderExecutionRequest,
    QuoteResponse,
)
from mock_providers.service.enums import QuoteDirection
from mock_providers.service.providers import ProviderConfig


def generate_quote(
    config: ProviderConfig,
    direction: QuoteDirection,
    pair: str,
    amount_out: Decimal,
) -> QuoteResponse:
    fee_rate = Decimal(str(random.uniform(config.fee_min, config.fee_max)))

    calc_amount_in = amount_out / (Decimal("1") - fee_rate)
    calc_amount_out = amount_out

    valid_until = datetime.now() + timedelta(seconds=settings.quote_ttl)
    return QuoteResponse(
        pair=pair,
        direction=direction,
        amount_in=calc_amount_in,
        amount_out=calc_amount_out,
        fee_rate=fee_rate,
        valid_until=valid_until.isoformat(),
    )


async def execute_order(config: ProviderConfig, _: OrderExecutionRequest) -> ExecuteResponse:
    latency = random.uniform(config.latency_min, config.latency_max)
    await asyncio.sleep(latency)

    rand = random.random()
    if rand < config.fail_prob:
        status = ExecutionStatus.FAIL
    elif rand < config.fail_prob + config.timeout_prob:
        status = ExecutionStatus.TIMEOUT
    else:
        status = ExecutionStatus.SUCCESS

    return ExecuteResponse(
        status=status,
        provider_ref=f"ref-{config.ref_prefix}-{uuid.uuid4().hex[:8]}",
    )
