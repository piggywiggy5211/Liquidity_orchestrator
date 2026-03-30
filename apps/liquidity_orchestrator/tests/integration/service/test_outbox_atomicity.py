from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from liquidity_orchestrator.database.uow import UnitOfWorkSqlAlchemy
from liquidity_orchestrator.domain.enums import OrderStatus, ProviderExecutionStatus, QuoteDirection
from liquidity_orchestrator.domain.metrics import InMemoryMetricsCollector
from liquidity_orchestrator.domain.models import Order, Outbox
from liquidity_orchestrator.domain.provider_dto import ProviderExecutionResponse
from liquidity_orchestrator.integrations.providers import PROVIDERS_MAP
from liquidity_orchestrator.service.dto import OrderCreateDTO, QuoteDTO
from liquidity_orchestrator.service.liquidity_service import LiquidityService
from sqlalchemy import select


@pytest.mark.asyncio
async def test_outbox_atomicity_rollback(db_session, session_factory):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP, InMemoryMetricsCollector())

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2",
    )
    created = await service.create_order(order_in)
    order_id = int(created.id)

    # mock fetching quotes
    quote = QuoteDTO(
        id=999,
        provider_name="ProviderA",
        amount_in=Decimal("100"),
        amount_out=Decimal("98"),
        fee_rate=Decimal("0.02"),
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
    )
    service._fetch_quotes_from_providers = AsyncMock(return_value=[quote])

    # Mock provider execution as successful
    with (
        patch(
            "liquidity_orchestrator.integrations.providers.provider_a.ProviderA.execute", new_callable=AsyncMock
        ) as mock_execute,
        patch("liquidity_orchestrator.integrations.providers.provider_b.ProviderB.execute", new=mock_execute),
        patch("liquidity_orchestrator.integrations.providers.provider_c.ProviderC.execute", new=mock_execute),
    ):
        mock_execute.return_value = ProviderExecutionResponse(
            status=ProviderExecutionStatus.SUCCESS, provider_ref="test-ref-123"
        )

        real_commit = uow.commit

        async def mock_commit_side_effect():
            if mock_commit_side_effect.call_count == 0:
                mock_commit_side_effect.call_count += 1
                return await real_commit()
            raise Exception("Database commit failed")

        mock_commit_side_effect.call_count = 0
        uow.commit = AsyncMock(side_effect=mock_commit_side_effect)

        # Execute order. It should fail with our error
        with pytest.raises(Exception, match="Database commit failed"):
            await service.execute_order(order_id)

    # Check atomicity in a NEW session
    async with session_factory() as session:
        # Order status should remain PROCESSING (not COMPLETED)
        db_order = await session.get(Order, order_id)
        assert db_order.status == OrderStatus.PROCESSING
        assert db_order.provider_ref is None

        # There should be no records in the outbox table for this order
        stmt = select(Outbox).where(Outbox.order_id == order_id)
        res = await session.execute(stmt)
        outbox_records = res.scalars().all()
        assert len(outbox_records) == 0


@pytest.mark.asyncio
async def test_outbox_atomicity_success(db_session, session_factory):
    """
    Additional test: verify that both changes are saved on regular success.
    """
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP, InMemoryMetricsCollector())

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2",
    )
    created = await service.create_order(order_in)
    order_id = int(created.id)

    quote = QuoteDTO(
        id=1,
        provider_name="ProviderA",
        amount_in=Decimal("100"),
        amount_out=Decimal("98"),
        fee_rate=Decimal("0.02"),
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
    )
    service._fetch_quotes_from_providers = AsyncMock(return_value=[quote])

    with (
        patch(
            "liquidity_orchestrator.integrations.providers.provider_a.ProviderA.execute", new_callable=AsyncMock
        ) as mock_execute,
        patch("liquidity_orchestrator.integrations.providers.provider_b.ProviderB.execute", new=mock_execute),
        patch("liquidity_orchestrator.integrations.providers.provider_c.ProviderC.execute", new=mock_execute),
    ):
        mock_execute.return_value = ProviderExecutionResponse(
            status=ProviderExecutionStatus.SUCCESS, provider_ref="success-ref"
        )

        await service.execute_order(order_id)

    # Check that BOTH changes are in the database
    async with session_factory() as session:
        db_order = await session.get(Order, order_id)
        assert db_order.status == OrderStatus.COMPLETED
        assert db_order.provider_ref == "success-ref"

        stmt = select(Outbox).where(Outbox.order_id == order_id)
        res = await session.execute(stmt)
        outbox_record = res.scalar_one()
        assert outbox_record is not None
        assert outbox_record.payload["order_id"] == order_id
