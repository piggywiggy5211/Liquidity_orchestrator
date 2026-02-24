from decimal import Decimal
from unittest.mock import AsyncMock, PropertyMock, patch

import pytest

from app.database.uow import UnitOfWorkSqlAlchemy
from app.service.dto import OrderCreateDTO, QuoteDTO
from app.service.enums import OrderStatus, QuoteDirection
from app.service.liquidity_service import LiquidityService
from app.service.models import Order
from app.service.providers import ExecutionStatus


@pytest.mark.asyncio
async def test_fallback_best_fails_next_succeeds(db_session, session_factory, clean_db):
    """
    Test scenario:
    1. Three providers provide quotes.
    2. ProviderA is scored better than ProviderB.
    3. ProviderA fails during execution (returns TIMEOUT).
    4. System falls back to ProviderB.
    5. ProviderB succeeds.
    6. Order status becomes COMPLETED.
    """
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, AsyncMock())

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

    # 2. Mock quotes from three providers
    # ProviderA has lower fee_rate, so it should be ranked higher
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

    # Mock scoring metrics to be identical for providers to ensure fee_rate is the tie-breaker/main factor
    mock_latency = {"ProviderA": 0.1, "ProviderB": 0.1, "ProviderC": 0.1}
    mock_timeouts = {"ProviderA": 0.0, "ProviderB": 0.0, "ProviderC": 0.0}

    with (
        patch.object(LiquidityService, "average_latency", new_callable=PropertyMock) as mock_lat,
        patch.object(LiquidityService, "timeout_percentage", new_callable=PropertyMock) as mock_tout,
    ):
        mock_lat.return_value = mock_latency
        mock_tout.return_value = mock_timeouts

        # 3. Mock provider execution
        with patch("app.service.providers.base.BaseProvider.execute", new_callable=AsyncMock) as mock_execute:
            # First call (ProviderA) returns TIMEOUT, second (ProviderB) returns SUCCESS
            mock_execute.side_effect = [
                {"status": ExecutionStatus.TIMEOUT, "provider_ref": "ref-fail-a"},
                {"status": ExecutionStatus.SUCCESS, "provider_ref": "ref-success-b"},
            ]

            # 4. Run execution
            await service.execute_order(order_id)

    # 5. Verify results in a new session
    async with session_factory() as session:
        # Order should be COMPLETED via ProviderB
        db_order = await session.get(Order, order_id)
        assert db_order.status == OrderStatus.COMPLETED
        assert db_order.provider_ref == "ref-success-b"
        assert db_order.quote_id == "102"
