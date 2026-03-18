from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from app.service.dto import QuoteDTO
from app.service.liquidity_service import LiquidityService


@pytest.fixture
def service():
    return LiquidityService(uow=MagicMock(), http_client=MagicMock())


def test_scoring_logic_ranking(service):
    # ProviderA: best rate, but frequent timeout 20%
    # ProviderB: medium rate, almost always works
    # ProviderC: worse rate, but low latency

    quotes = [
        QuoteDTO(provider_name="ProviderA", fee_rate=Decimal("0.001"), amount_in=Decimal("100")),
        QuoteDTO(provider_name="ProviderB", fee_rate=Decimal("0.01"), amount_in=Decimal("100")),
        QuoteDTO(provider_name="ProviderC", fee_rate=Decimal("0.02"), amount_in=Decimal("100")),
    ]

    # Metrics
    # ProviderA: fee=0.001 (min), latency=0.5 (max), timeout=20.0 (max)
    # ProviderB: fee=0.01 (mid), latency=0.5 (max), timeout=0.0 (min)
    # ProviderC: fee=0.02 (max), latency=0.1 (min), timeout=0.0 (min)

    mock_latency = {"ProviderA": 0.5, "ProviderB": 0.5, "ProviderC": 0.1}
    mock_timeouts = {"ProviderA": 20.0, "ProviderB": 0.0, "ProviderC": 0.0}

    with (
        patch.object(LiquidityService, "average_latency", new_callable=PropertyMock) as mock_lat,
        patch.object(LiquidityService, "timeout_percentage", new_callable=PropertyMock) as mock_tout,
    ):
        mock_lat.return_value = mock_latency
        mock_tout.return_value = mock_timeouts

        plan = service._build_execution_plan(quotes, order_id=111)

        # Expected order: ProviderB, ProviderC, ProviderA
        assert plan[0].provider_name == "ProviderB"
        assert plan[1].provider_name == "ProviderC"
        assert plan[2].provider_name == "ProviderA"


def test_scoring_identical_values(service):
    quotes = [
        QuoteDTO(provider_name="P1", fee_rate=Decimal("0.01"), amount_in=Decimal("100")),
        QuoteDTO(provider_name="P2", fee_rate=Decimal("0.01"), amount_in=Decimal("100")),
    ]

    mock_latency = {"P1": 0.5, "P2": 0.5}
    mock_timeouts = {"P1": 2.0, "P2": 2.0}

    with (
        patch.object(LiquidityService, "average_latency", new_callable=PropertyMock) as mock_lat,
        patch.object(LiquidityService, "timeout_percentage", new_callable=PropertyMock) as mock_tout,
    ):
        mock_lat.return_value = mock_latency
        mock_tout.return_value = mock_timeouts

        plan = service._build_execution_plan(quotes, order_id=111)
        assert len(plan) == 2
        # When everything is identical, order doesn't matter
        assert {p.provider_name for p in plan} == {"P1", "P2"}
