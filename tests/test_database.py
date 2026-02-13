from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.service.models import Order, Outbox
from app.service.enums import OrderStatus, QuoteDirection, OutboxEventType
from app.database.uow import UnitOfWork


@pytest.mark.asyncio
async def test_uow_order_creation(session_factory, clean_db):
    uow = UnitOfWork(session_factory)
    async with uow:
        order = await uow.orders.create(
            quote_id="q1",
            status=OrderStatus.NEW,
            provider_name="test_provider",
        )
        await uow.session.flush()  # Populate ID
        order_id = order.id
        await uow.commit()

    # Verify in new session
    async with session_factory() as session:
        repo_order = await session.get(Order, order_id)
        assert repo_order is not None
        assert repo_order.quote_id == "q1"
        assert repo_order.status == OrderStatus.NEW


@pytest.mark.asyncio
async def test_uow_quote_and_outbox(session_factory, clean_db):
    uow = UnitOfWork(session_factory)
    async with uow:
        await uow.quotes.create(
            direction=QuoteDirection.ON_RAMP,
            pair="usd-usdt",
            amount_in=Decimal("100"),
            amount_out=Decimal("99"),
            amount_fee=Decimal("1"),
            provider_name="test_provider",
            valid_until=datetime.now() + timedelta(minutes=10),
        )

        order = await uow.orders.create(
            quote_id="q2",
            status=OrderStatus.COMPLETED,
            provider_name="test_provider",
        )
        await uow.session.flush()  # to get order.id

        await uow.outbox.create(
            order_id=order.id,
            event_type=OutboxEventType.ORDER_COMPLETED,
            payload={"amount_in": 100, "provider_name": "test_provider"},
        )
        await uow.commit()

    # Verify
    async with session_factory() as session:
        res = await session.execute(select(Order).where(Order.quote_id == "q2"))
        db_order = res.scalar_one()
        assert db_order.status == OrderStatus.COMPLETED

        # Check outbox
        res = await session.execute(select(Outbox).where(Outbox.order_id == db_order.id))
        db_outbox = res.scalar_one()
        assert db_outbox.event_type == OutboxEventType.ORDER_COMPLETED
        assert db_outbox.payload["amount_in"] == 100
