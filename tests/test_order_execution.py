from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.database.uow import UnitOfWorkSqlAlchemy
from app.domain.enums import OrderStatus, QuoteDirection
from app.domain.models import Order
from app.service.dto import OrderCreateDTO
from app.service.liquidity_service import LiquidityService
from app.service.providers import ExecutionStatus


@pytest.mark.asyncio
async def test_order_execution_full_cycle_success(db_session, session_factory, mock_asyncio_sleep):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, AsyncMock())

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2",
    )

    # Mock execute in BaseProvider
    with patch("app.service.providers.base.BaseProvider.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = {"status": ExecutionStatus.SUCCESS, "provider_ref": "test-ref-123"}

        created = await service.create_order(order_in)
        await service.execute_order(int(created.id))

    # Verify results in DB
    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.COMPLETED
        assert order.provider_ref == "test-ref-123"
        assert order.incoming_amount == Decimal("100")
        assert order.outgoing_amount == Decimal("98")  # 100 - (100 * 0.02)


@pytest.mark.asyncio
async def test_order_execution_retry_logic(db_session, session_factory, mock_asyncio_sleep):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, AsyncMock())

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2",
    )

    with patch("app.service.providers.base.BaseProvider.execute", new_callable=AsyncMock) as mock_execute:
        # First provider (in plan) will return TIMEOUT, second SUCCESS
        mock_execute.side_effect = [
            {"status": ExecutionStatus.TIMEOUT, "provider_ref": "ref-fail"},
            {"status": ExecutionStatus.SUCCESS, "provider_ref": "ref-success"},
        ]

        created = await service.create_order(order_in)
        await service.execute_order(int(created.id))

    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.COMPLETED
        # Check that there were 2 calls (if there were >= 2 providers in plan)
        assert mock_execute.call_count == 2
        assert order.provider_ref == "ref-success"


@pytest.mark.asyncio
async def test_order_execution_all_fail(db_session, session_factory, mock_asyncio_sleep):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, AsyncMock())

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2",
    )

    with patch("app.service.providers.base.BaseProvider.execute", new_callable=AsyncMock) as mock_execute:
        # All providers return FAIL
        mock_execute.return_value = {"status": ExecutionStatus.FAIL, "provider_ref": "ref-fail"}

        created = await service.create_order(order_in)
        await service.execute_order(int(created.id))

    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.FAILED
        # Should be as many calls as providers that returned quotes (usually 3)
        assert mock_execute.call_count >= 1
