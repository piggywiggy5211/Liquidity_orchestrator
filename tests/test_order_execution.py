import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from app.service.liquidity_service import LiquidityService
from app.service.dto import OrderCreateDTO
from app.service.enums import QuoteDirection, OrderStatus
from app.service.providers import ExecutionStatus, PROVIDERS_LIST
from app.database.uow import UnitOfWork
from app.service.models import Order

@pytest.mark.asyncio
async def test_order_execution_full_cycle_success(db_session, session_factory, clean_db):
    uow = UnitOfWork(session_factory)
    service = LiquidityService(uow, AsyncMock())
    
    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2"
    )

    # Замокаем sleep и random, чтобы всё было быстро и предсказуемо
    with patch("asyncio.sleep", AsyncMock()):
        # Замокаем execute в BaseProvider
        with patch("app.service.providers.base.BaseProvider.execute", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "status": ExecutionStatus.SUCCESS,
                "provider_ref": "test-ref-123"
            }
            
            created = await service.create_order(order_in)
            await service.execute_order(int(created.id))

    # Проверяем результат в БД
    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.COMPLETED
        assert order.provider_ref == "test-ref-123"
        assert order.incoming_amount == Decimal("100")
        assert order.outgoing_amount == Decimal("98") # 100 - (100 * 0.02)

@pytest.mark.asyncio
async def test_order_execution_retry_logic(db_session, session_factory, clean_db):
    uow = UnitOfWork(session_factory)
    service = LiquidityService(uow, AsyncMock())
    
    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2"
    )

    with patch("asyncio.sleep", AsyncMock()):
        with patch("app.service.providers.base.BaseProvider.execute", new_callable=AsyncMock) as mock_execute:
            # Первый провайдер (в плане) вернет TIMEOUT, второй SUCCESS
            mock_execute.side_effect = [
                {"status": ExecutionStatus.TIMEOUT, "provider_ref": "ref-fail"},
                {"status": ExecutionStatus.SUCCESS, "provider_ref": "ref-success"},
            ]
            
            created = await service.create_order(order_in)
            await service.execute_order(int(created.id))

    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.COMPLETED
        # Проверяем, что вызовов было 2 (если в плане было >= 2 провайдеров)
        assert mock_execute.call_count == 2
        assert order.provider_ref == "ref-success"

@pytest.mark.asyncio
async def test_order_execution_all_fail(db_session, session_factory, clean_db):
    uow = UnitOfWork(session_factory)
    service = LiquidityService(uow, AsyncMock())
    
    order_in = OrderCreateDTO(
        direction=QuoteDirection.ON_RAMP,
        pair="EUR-USD",
        amount=Decimal("100"),
        incoming_account="acc1",
        outgoing_account="acc2"
    )

    with patch("asyncio.sleep", AsyncMock()):
        with patch("app.service.providers.base.BaseProvider.execute", new_callable=AsyncMock) as mock_execute:
            # Все провайдеры возвращают FAIL
            mock_execute.return_value = {"status": ExecutionStatus.FAIL, "provider_ref": "ref-fail"}
            
            created = await service.create_order(order_in)
            await service.execute_order(int(created.id))

    async with session_factory() as session:
        order = await session.get(Order, int(created.id))
        assert order.status == OrderStatus.FAILED
        # Должно быть столько вызовов, сколько провайдеров вернули квоты (обычно 3)
        assert mock_execute.call_count >= 1
