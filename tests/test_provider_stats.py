import pytest
import time
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from app.service.liquidity_service import LiquidityService
from app.service.dto import OrderCreateDTO, QuoteDTO
from app.service.enums import QuoteDirection
from app.service.providers import ExecutionStatus
from app.database.uow import UnitOfWorkSqlAlchemy
from app.service.mixins import TaskWrapperMixin, ProviderStatsMixin

@pytest.fixture(autouse=True)
def clear_stats():
    ProviderStatsMixin._stats.clear()

@pytest.mark.asyncio
async def test_provider_stats_mixin_logic(db_session, session_factory, clean_db):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, AsyncMock())
    
    # Test recording stats directly first to verify mixin logic
    service.record_execution("ProviderA", 0.1, ExecutionStatus.SUCCESS)
    service.record_execution("ProviderA", 0.2, ExecutionStatus.TIMEOUT)
    service.record_execution("ProviderB", 0.5, ExecutionStatus.SUCCESS)
    
    assert service.average_latency["ProviderA"] == pytest.approx(0.1)
    assert service.average_latency["ProviderB"] == pytest.approx(0.5)
    
    assert service.timeout_percentage["ProviderA"] == 50.0
    assert service.timeout_percentage["ProviderB"] == 0.0

@pytest.mark.asyncio
async def test_provider_stats_moving_window(db_session, session_factory, clean_db):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, AsyncMock())
    
    with patch("time.time") as mock_time:
        start_t = 1000.0
        mock_time.return_value = start_t
        
        service.record_execution("ProviderA", 0.1, ExecutionStatus.SUCCESS)
        
        # Move time forward by 30 seconds
        mock_time.return_value = start_t + 30.0
        service.record_execution("ProviderA", 0.2, ExecutionStatus.SUCCESS)
        
        # Move time forward by another 40 seconds (total 70s from start)
        # First record should be cleaned up (window is 60s)
        mock_time.return_value = start_t + 70.0
        assert service.average_latency["ProviderA"] == pytest.approx(0.2)

@pytest.mark.asyncio
async def test_provider_stats_integration_in_execute_order(db_session, session_factory, clean_db):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, AsyncMock())
    
    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2"
    )
    
    # We need to mock _fetch_quotes_from_providers to return specific quotes
    # so we know which providers will be in the execution plan.
    mock_quotes = [
        QuoteDTO(id=1, provider_name="ProviderA", fee_rate=Decimal("0.01"), amount_in=Decimal("101")),
        QuoteDTO(id=2, provider_name="ProviderB", fee_rate=Decimal("0.02"), amount_in=Decimal("102")),
    ]
    
    with patch.object(LiquidityService, "_fetch_quotes_from_providers", return_value=mock_quotes):
        with patch("app.service.providers.provider_a.ProviderA.execute", new_callable=AsyncMock) as mock_exec_a:
            with patch("app.service.providers.provider_b.ProviderB.execute", new_callable=AsyncMock) as mock_exec_b:
                mock_exec_a.return_value = {"status": ExecutionStatus.TIMEOUT, "provider_ref": "ref1"}
                mock_exec_b.return_value = {"status": ExecutionStatus.SUCCESS, "provider_ref": "ref2"}
                
                # Mock time to control latency measurement
                # Mock time to control latency measurement
                with patch("time.time") as mock_time, patch("time.perf_counter") as mock_perf:
                    t = 2000.0
                    p = 100.0
                    # Mock values for time.time() (used for record timestamps and cleanup):
                    mock_time.side_effect = [
                        t + 0.2, t + 0.2, # ProviderA
                        t + 0.6, t + 0.6, # ProviderB
                    ] + [t + 0.7] * 50

                    # Mock values for time.perf_counter() (used for latency calculation):
                    mock_perf.side_effect = [
                        p + 0.1, p + 0.2, # ProviderA
                        p + 0.3, p + 0.6, # ProviderB
                    ]
                    
                    created = await service.create_order(order_in)
                    await service.execute_order(int(created.id))
                    
                    # We access properties. Each access consumes one value from side_effect if it's called.
                    avg_lat = service.average_latency
                    t_perc = service.timeout_percentage

                    assert avg_lat["ProviderA"] == 0.0
                    assert avg_lat["ProviderB"] == pytest.approx(0.3)
                    assert t_perc["ProviderA"] == 100.0
                    assert t_perc["ProviderB"] == 0.0
