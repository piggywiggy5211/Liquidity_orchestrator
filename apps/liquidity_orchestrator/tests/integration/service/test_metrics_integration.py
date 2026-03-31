import asyncio
from datetime import datetime
from decimal import Decimal

import pytest
from liquidity_orchestrator.database.uow import UnitOfWorkSqlAlchemy
from liquidity_orchestrator.domain.enums import ProviderExecutionStatus, QuoteDirection
from liquidity_orchestrator.domain.metrics import InMemoryMetricsCollector
from liquidity_orchestrator.domain.provider_dto import (
    ProviderExecutionResponse,
    ProviderGetQuoteRequest,
    ProviderOrderExecutionRequest,
    ProviderQuoteResponse,
)
from liquidity_orchestrator.integrations.providers.base import BaseProvider
from liquidity_orchestrator.service.dto import OrderCreateDTO
from liquidity_orchestrator.service.liquidity_service import LiquidityService


class FakeSuccessProvider(BaseProvider):
    name = "FakeSuccess"

    async def get_quote(self, request: ProviderGetQuoteRequest) -> ProviderQuoteResponse:
        return ProviderQuoteResponse(
            direction=request.direction,
            pair=request.pair,
            amount_in=Decimal("100"),
            amount_out=Decimal("99"),
            fee_rate=Decimal("0.02"),  # Higher fee, will be executed second
            valid_until=datetime.now(),
        )

    async def execute(self, order: ProviderOrderExecutionRequest) -> ProviderExecutionResponse:
        # Simulate slight latency
        await asyncio.sleep(0.2)
        return ProviderExecutionResponse(status=ProviderExecutionStatus.SUCCESS, provider_ref="success-ref")


class FakeTimeoutProvider(BaseProvider):
    name = "FakeTimeout"

    async def get_quote(self, request: ProviderGetQuoteRequest) -> ProviderQuoteResponse:
        return ProviderQuoteResponse(
            direction=request.direction,
            pair=request.pair,
            amount_in=Decimal("100"),
            amount_out=Decimal("99"),
            fee_rate=Decimal("0.01"),  # Lower fee, will be executed first
            valid_until=datetime.now(),
        )

    async def execute(self, order: ProviderOrderExecutionRequest) -> ProviderExecutionResponse:
        # Simulate slight latency
        await asyncio.sleep(0.1)
        return ProviderExecutionResponse(status=ProviderExecutionStatus.TIMEOUT, provider_ref="timeout-ref")


@pytest.mark.asyncio
async def test_liquidity_service_metrics_integration_with_fakes(db_session, session_factory):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    metrics_collector = InMemoryMetricsCollector()

    FakeSuccessProvider.metrics_collector = metrics_collector
    FakeSuccessProvider.httpx_client = None  # Not used in fake

    FakeTimeoutProvider.metrics_collector = metrics_collector
    FakeTimeoutProvider.httpx_client = None

    fake_providers_map = {
        "FakeSuccess": FakeSuccessProvider,
        "FakeTimeout": FakeTimeoutProvider,
    }

    service = LiquidityService(uow, fake_providers_map, metrics_collector, Decimal("0.02"))

    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="BTC-USD",
        amount=Decimal("100.0"),
        incoming_account="acct-1",
        outgoing_account="acct-2",
    )

    created = await service.create_order(order_in)
    await service.execute_order(int(created.id))

    # Check metrics were recorded correctly directly on the collector
    assert metrics_collector.timeout_percentage["FakeTimeout"] == 100.0
    assert metrics_collector.timeout_percentage["FakeSuccess"] == 0.0

    assert metrics_collector.average_latency["FakeSuccess"] > 0.1
    assert metrics_collector.average_latency["FakeTimeout"] == 0.0
