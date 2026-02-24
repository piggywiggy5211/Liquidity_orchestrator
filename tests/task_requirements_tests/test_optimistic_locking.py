import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.database.uow import UnitOfWorkSqlAlchemy
from app.service.dto import OrderCreateDTO
from app.service.enums import QuoteDirection
from app.service.liquidity_service import LiquidityService


@pytest.mark.asyncio
async def test_execute_order_parallel_conflict(session_factory, clean_db):
    """
    Verify that parallel calls to execute_order trigger
    optimistic locking and raise an Exception.
    """
    # 1. Create an order
    async with session_factory() as sess:
        uow = UnitOfWorkSqlAlchemy(session_factory, sess)
        service = LiquidityService(uow, AsyncMock())
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

        # Mock _fetch_quotes_from_providers to avoid real network calls
        with patch(
            "app.service.liquidity_service.LiquidityService._fetch_quotes_from_providers",
            new_callable=AsyncMock,
            return_value=[],
        ):
            service1 = LiquidityService(uow1, AsyncMock())
            service2 = LiquidityService(uow2, AsyncMock())
            service3 = LiquidityService(uow3, AsyncMock())

            # Run in parallel.
            # Due to asyncio.gather and await inside execute_order,
            # sessions will have time to read the same data version before the first commit.
            results = await asyncio.gather(
                service1.execute_order(order_id),
                service2.execute_order(order_id),
                service3.execute_order(order_id),
                return_exceptions=True,
            )

    # 3. Analyze results
    exceptions = [r for r in results if isinstance(r, Exception)]

    # One or two calls should fail with a locking error
    assert len(exceptions) >= 1
    # Verify that at least one call succeeded (or failed due to something other than optimistic locking)
    successes = [r for r in results if r is None]
    assert len(successes) >= 1
