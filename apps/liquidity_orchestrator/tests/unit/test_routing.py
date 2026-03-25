from datetime import datetime
from decimal import Decimal

from liquidity_orchestrator.domain.enums import QuoteDirection
from liquidity_orchestrator.domain.models import Quote
from liquidity_orchestrator.domain.routing import build_execution_plan


def test_build_execution_plan_ranking():
    # ProviderA: best rate, but frequent timeout 20%
    # ProviderB: medium rate, almost always works
    # ProviderC: worse rate, but low latency

    quotes = [
        Quote(
            provider_name="ProviderA",
            fee_rate=Decimal("0.001"),
            amount_in=Decimal("100"),
            amount_out=Decimal("99.9"),
            direction=QuoteDirection.ON_RAMP,
            pair="USDT-USD",
            valid_until=datetime.now(),
            id=1,
        ),
        Quote(
            provider_name="ProviderB",
            fee_rate=Decimal("0.01"),
            amount_in=Decimal("100"),
            amount_out=Decimal("99"),
            direction=QuoteDirection.ON_RAMP,
            pair="USDT-USD",
            valid_until=datetime.now(),
            id=2,
        ),
        Quote(
            provider_name="ProviderC",
            fee_rate=Decimal("0.02"),
            amount_in=Decimal("100"),
            amount_out=Decimal("98"),
            direction=QuoteDirection.ON_RAMP,
            pair="USDT-USD",
            valid_until=datetime.now(),
            id=3,
        ),
    ]

    average_latencies = {"ProviderA": 0.5, "ProviderB": 0.5, "ProviderC": 0.1}
    timeout_percentages = {"ProviderA": 20.0, "ProviderB": 0.0, "ProviderC": 0.0}

    plan = build_execution_plan(quotes, average_latencies, timeout_percentages, order_id=111)

    # Expected order: ProviderB, ProviderC, ProviderA
    assert plan[0].provider_name == "ProviderB"
    assert plan[1].provider_name == "ProviderC"
    assert plan[2].provider_name == "ProviderA"


def test_build_execution_plan_identical_values():
    quotes = [
        Quote(
            provider_name="P1",
            fee_rate=Decimal("0.01"),
            amount_in=Decimal("100"),
            amount_out=Decimal("99"),
            direction=QuoteDirection.ON_RAMP,
            pair="USDT-USD",
            valid_until=datetime.now(),
            id=1,
        ),
        Quote(
            provider_name="P2",
            fee_rate=Decimal("0.01"),
            amount_in=Decimal("100"),
            amount_out=Decimal("99"),
            direction=QuoteDirection.ON_RAMP,
            pair="USDT-USD",
            valid_until=datetime.now(),
            id=2,
        ),
    ]

    average_latencies = {"P1": 0.5, "P2": 0.5}
    timeout_percentages = {"P1": 2.0, "P2": 2.0}

    plan = build_execution_plan(quotes, average_latencies, timeout_percentages, order_id=111)
    assert len(plan) == 2
    assert {p.provider_name for p in plan} == {"P1", "P2"}


def test_build_execution_plan_empty_quotes():
    plan = build_execution_plan([], {}, {}, order_id=111)
    assert plan == []
