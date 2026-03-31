import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from liquidity_orchestrator.database.uow import UnitOfWorkSqlAlchemy
from liquidity_orchestrator.domain.enums import QuoteDirection
from liquidity_orchestrator.domain.metrics import InMemoryMetricsCollector
from liquidity_orchestrator.integrations.providers import PROVIDERS_MAP
from liquidity_orchestrator.service.dto import OrderCreateDTO
from liquidity_orchestrator.service.liquidity_service import LiquidityService


@pytest.mark.asyncio
async def test_execute_order_parallel_conflict(session_factory):
    """
    Verify that parallel calls to execute_order trigger
    optimistic locking and raise an Exception.
    """
    # 1. Create an order
    async with session_factory() as sess:
        uow = UnitOfWorkSqlAlchemy(session_factory, sess)
        service = LiquidityService(uow, PROVIDERS_MAP, InMemoryMetricsCollector(), Decimal("0.02"))
        order_in = OrderCreateDTO(
            direction=QuoteDirection.ON_RAMP,
            pair="EUR-USD",
            amount=Decimal("100"),
            incoming_account="acc1",
            outgoing_account="acc2",
        )
        created = await service.create_order(order_in)
        order_id = created.id

    # 2. Prepare multiple services with DIFFERENT sessions
    async with session_factory() as sess1, session_factory() as sess2, session_factory() as sess3:
        uow1 = UnitOfWorkSqlAlchemy(session_factory, sess1)
        uow2 = UnitOfWorkSqlAlchemy(session_factory, sess2)
        uow3 = UnitOfWorkSqlAlchemy(session_factory, sess3)

        with patch(
            "liquidity_orchestrator.service.liquidity_service.LiquidityService._fetch_quotes_from_providers",
            new_callable=AsyncMock,
            return_value=[],
        ):
            service1 = LiquidityService(uow1, PROVIDERS_MAP, InMemoryMetricsCollector(), Decimal("0.02"))
            service2 = LiquidityService(uow2, PROVIDERS_MAP, InMemoryMetricsCollector(), Decimal("0.02"))
            service3 = LiquidityService(uow3, PROVIDERS_MAP, InMemoryMetricsCollector(), Decimal("0.02"))

            results = await asyncio.gather(
                service1.execute_order(order_id),
                service2.execute_order(order_id),
                service3.execute_order(order_id),
                return_exceptions=True,
            )

    # 3. Analyze results
    exceptions = [r for r in results if isinstance(r, Exception)]
    assert len(exceptions) >= 1
    successes = [r for r in results if r is None]
    assert len(successes) >= 1
