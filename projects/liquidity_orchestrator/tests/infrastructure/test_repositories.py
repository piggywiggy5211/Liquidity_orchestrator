from decimal import Decimal

import pytest
from database.uow import UnitOfWorkSqlAlchemy
from domain.enums import OrderStatus, QuoteDirection
from domain.models import Order
from service.dto import OrderDTO


@pytest.mark.asyncio
async def test_get_all_functionality(db_session, session_factory):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)

    # 1. Add test data
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

    # 2. Call get_all
    async with uow:
        models = await uow.orders.get_all()

        # Check types and count
        assert len(models) == 5

        # Check models content and to_dto conversion
        for model in models:
            assert isinstance(model, Order)
            dto = OrderDTO.model_validate(model)
            assert isinstance(dto, OrderDTO)
            assert dto.incoming_amount == Decimal("100")
