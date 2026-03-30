from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from liquidity_orchestrator.database.uow import UnitOfWorkSqlAlchemy
from liquidity_orchestrator.domain.enums import OrderStatus, ProviderExecutionStatus, QuoteDirection
from liquidity_orchestrator.domain.metrics import InMemoryMetricsCollector
from liquidity_orchestrator.domain.models import Order
from liquidity_orchestrator.domain.provider_dto import ProviderExecutionResponse
from liquidity_orchestrator.integrations.providers import PROVIDERS_MAP
from liquidity_orchestrator.service.dto import OrderCreateDTO, QuoteDTO
from liquidity_orchestrator.service.liquidity_service import LiquidityService


@pytest.mark.asyncio
async def test_liquidity_service_basic_flow(db_session, session_factory, mock_asyncio_sleep):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP, InMemoryMetricsCollector())

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="USDT-USD",
        amount=Decimal("100.0"),
        incoming_account="acct-1",
        outgoing_account="acct-2",
    )

    with (
        patch(
            "liquidity_orchestrator.integrations.providers.provider_a.ProviderA.execute", new_callable=AsyncMock
        ) as mock_execute,
        patch("liquidity_orchestrator.integrations.providers.provider_b.ProviderB.execute", new=mock_execute),
        patch("liquidity_orchestrator.integrations.providers.provider_c.ProviderC.execute", new=mock_execute),
    ):
        mock_execute.return_value = ProviderExecutionResponse(
            status=ProviderExecutionStatus.SUCCESS, provider_ref="ref-123"
        )

        quote = QuoteDTO(
            id=1,
            provider_name="ProviderA",
            amount_in=Decimal("100"),
            amount_out=Decimal("100"),
            fee_rate=Decimal("0.02"),
            direction=order_in.direction,
            pair=order_in.pair,
        )
        service._fetch_quotes_from_providers = AsyncMock(return_value=[quote])
        created = await service.create_order(order_in)
        assert created.status == "NEW"
        assert created.incoming_amount == Decimal("100.0")
        assert created.outgoing_amount == Decimal("98.0")
        await service.execute_order(int(created.id))

    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.COMPLETED
        assert order.incoming_amount == Decimal("100.0")
        assert order.outgoing_amount == Decimal("98.0")


@pytest.mark.asyncio
async def test_order_execution_full_cycle_success(db_session, session_factory, mock_asyncio_sleep):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP, InMemoryMetricsCollector())

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2",
    )

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

        quote = QuoteDTO(
            id=1,
            provider_name="ProviderA",
            amount_in=Decimal("100"),
            amount_out=Decimal("100"),
            fee_rate=Decimal("0.02"),
            direction=order_in.direction,
            pair=order_in.pair,
        )
        service._fetch_quotes_from_providers = AsyncMock(return_value=[quote])
        created = await service.create_order(order_in)
        await service.execute_order(int(created.id))

    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.COMPLETED
        assert order.provider_ref == "test-ref-123"
        assert order.incoming_amount == Decimal("100")
        assert order.outgoing_amount == Decimal("98")


@pytest.mark.asyncio
async def test_order_execution_retry_logic(db_session, session_factory, mock_asyncio_sleep):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP, InMemoryMetricsCollector())

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2",
    )

    with (
        patch(
            "liquidity_orchestrator.integrations.providers.provider_a.ProviderA.execute", new_callable=AsyncMock
        ) as mock_execute,
        patch("liquidity_orchestrator.integrations.providers.provider_b.ProviderB.execute", new=mock_execute),
        patch("liquidity_orchestrator.integrations.providers.provider_c.ProviderC.execute", new=mock_execute),
    ):
        mock_execute.side_effect = [
            ProviderExecutionResponse(status=ProviderExecutionStatus.TIMEOUT, provider_ref="ref-fail"),
            ProviderExecutionResponse(status=ProviderExecutionStatus.SUCCESS, provider_ref="ref-success"),
        ]

        quote1 = QuoteDTO(
            id=1,
            provider_name="ProviderA",
            amount_in=Decimal("100"),
            amount_out=Decimal("100"),
            fee_rate=Decimal("0.02"),
            direction=order_in.direction,
            pair=order_in.pair,
        )
        quote2 = QuoteDTO(
            id=2,
            provider_name="ProviderB",
            amount_in=Decimal("100"),
            amount_out=Decimal("100"),
            fee_rate=Decimal("0.02"),
            direction=order_in.direction,
            pair=order_in.pair,
        )
        service._fetch_quotes_from_providers = AsyncMock(return_value=[quote1, quote2])
        created = await service.create_order(order_in)
        await service.execute_order(int(created.id))

    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.COMPLETED
        assert mock_execute.call_count == 2
        assert order.provider_ref == "ref-success"


@pytest.mark.asyncio
async def test_order_execution_all_fail(db_session, session_factory, mock_asyncio_sleep):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP, InMemoryMetricsCollector())

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2",
    )

    with (
        patch(
            "liquidity_orchestrator.integrations.providers.provider_a.ProviderA.execute", new_callable=AsyncMock
        ) as mock_execute,
        patch("liquidity_orchestrator.integrations.providers.provider_b.ProviderB.execute", new=mock_execute),
        patch("liquidity_orchestrator.integrations.providers.provider_c.ProviderC.execute", new=mock_execute),
    ):
        mock_execute.return_value = ProviderExecutionResponse(
            status=ProviderExecutionStatus.DECLINE, provider_ref="ref-fail"
        )

        quote = QuoteDTO(
            id=1,
            provider_name="ProviderA",
            amount_in=Decimal("100"),
            amount_out=Decimal("100"),
            fee_rate=Decimal("0.02"),
            direction=order_in.direction,
            pair=order_in.pair,
        )
        service._fetch_quotes_from_providers = AsyncMock(return_value=[quote])
        created = await service.create_order(order_in)
        await service.execute_order(int(created.id))

    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.FAILED
        assert mock_execute.call_count >= 1
