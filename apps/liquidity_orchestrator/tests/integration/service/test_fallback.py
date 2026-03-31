from decimal import Decimal
from unittest.mock import AsyncMock, PropertyMock, patch

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
async def test_fallback_best_fails_next_succeeds(db_session, session_factory):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP, InMemoryMetricsCollector(stats_window_seconds=60), Decimal("0.02"))

    # 1. Create order
    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="BTC-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2",
    )
    created = await service.create_order(order_in)
    order_id = int(created.id)

    # 2. Mock quotes
    quote_a = QuoteDTO(
        id=101,
        provider_name="ProviderA",
        amount_in=Decimal("100"),
        amount_out=Decimal("99"),
        fee_rate=Decimal("0.01"),
        direction=QuoteDirection.ON_RAMP,
        pair="BTC-USD",
    )
    quote_b = QuoteDTO(
        id=102,
        provider_name="ProviderB",
        amount_in=Decimal("100"),
        amount_out=Decimal("98"),
        fee_rate=Decimal("0.02"),
        direction=QuoteDirection.ON_RAMP,
        pair="BTC-USD",
    )
    quote_c = QuoteDTO(
        id=103,
        provider_name="ProviderC",
        amount_in=Decimal("100"),
        amount_out=Decimal("97"),
        fee_rate=Decimal("0.03"),
        direction=QuoteDirection.ON_RAMP,
        pair="BTC-USD",
    )

    service._fetch_quotes_from_providers = AsyncMock(return_value=[quote_a, quote_b, quote_c])

    mock_latency = {"ProviderA": 0.1, "ProviderB": 0.1, "ProviderC": 0.1}
    mock_timeouts = {"ProviderA": 0.0, "ProviderB": 0.0, "ProviderC": 0.0}

    with (
        patch.object(InMemoryMetricsCollector, "average_latency", new_callable=PropertyMock) as mock_lat,
        patch.object(InMemoryMetricsCollector, "timeout_percentage", new_callable=PropertyMock) as mock_tout,
    ):
        mock_lat.return_value = mock_latency
        mock_tout.return_value = mock_timeouts

        with (
            patch(
                "liquidity_orchestrator.integrations.providers.provider_a.ProviderA.execute", new_callable=AsyncMock
            ) as mock_execute,
            patch("liquidity_orchestrator.integrations.providers.provider_b.ProviderB.execute", new=mock_execute),
            patch("liquidity_orchestrator.integrations.providers.provider_c.ProviderC.execute", new=mock_execute),
        ):
            mock_execute.side_effect = [
                ProviderExecutionResponse(status=ProviderExecutionStatus.TIMEOUT, provider_ref="ref-fail-a"),
                ProviderExecutionResponse(status=ProviderExecutionStatus.SUCCESS, provider_ref="ref-success-b"),
            ]

            await service.execute_order(order_id)

    async with session_factory() as session:
        db_order = await session.get(Order, order_id)
        assert db_order.status == OrderStatus.COMPLETED
        assert db_order.provider_ref == "ref-success-b"
        assert db_order.quote_id == "102"
