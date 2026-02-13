import pytest
from decimal import Decimal
from sqlalchemy import select
from app.service.models import Order
from app.service.enums import OrderStatus, QuoteDirection
from app.database.uow import UnitOfWork
from app.service.dto import OrderDTO
from app.database.repositories.base import LazyDtoSequence

@pytest.mark.asyncio
async def test_get_all_functionality(session_factory, clean_db):
    uow = UnitOfWork(session_factory)
    
    # 1. Добавляем тестовые данные
    orders_data = [
        Order(
            incoming_amount=Decimal("100"),
            outgoing_amount=Decimal("98"),
            incoming_account=f"acct-in-{i}",
            outgoing_account=f"acct-out-{i}",
            direction=QuoteDirection.ON_RAMP,
            pair="USDT-USD",
            status=OrderStatus.NEW,
        )
        for i in range(5)
    ]
    
    async with uow:
        for order in orders_data:
            uow.orders.add(order)
        await uow.commit()

    # 2. Вызываем get_all
    async with uow:
        models, dtos = await uow.orders.get_all()
        
        # Проверяем типы и количество
        assert len(models) == 5
        assert len(dtos) == 5
        assert isinstance(dtos, LazyDtoSequence)
        
        # Проверяем содержимое моделей
        for model in models:
            assert isinstance(model, Order)
            
        # 3. Тестируем индексацию LazyDtoSequence
        first_dto = dtos[0]
        assert isinstance(first_dto, OrderDTO)
        assert first_dto.incoming_account == "acct-in-0"
        
        # 4. Тестируем итерацию
        for i, dto in enumerate(dtos):
            assert isinstance(dto, OrderDTO)
            assert dto.incoming_account == f"acct-in-{i}"
            
        # 5. Тестируем срезы (slices)
        subset = dtos[1:3]
        assert isinstance(subset, list)
        assert len(subset) == 2
        assert subset[0].incoming_account == "acct-in-1"
        assert subset[1].incoming_account == "acct-in-2"
        
        # 6. Проверяем len()
        assert len(dtos) == 5
