from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.service.models import Order, Outbox, Quote
from app.service.enums import OrderStatus, QuoteDirection, OutboxEventType
from app.database.uow import UnitOfWorkSqlAlchemy


@pytest.mark.asyncio
async def test_uow_order_creation(db_session, session_factory, clean_db):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    async with uow:
        order = Order(
            incoming_amount=Decimal("100"),
            outgoing_amount=Decimal("98"),
            incoming_account="acct-1",
            outgoing_account="acct-2",
            direction=QuoteDirection.ON_RAMP,
            pair="USDT-USD",
            quote_id="q1",
            status=OrderStatus.NEW,
        )
        uow.orders.add(order)
        await uow._session.flush()  # Populate ID
        order_id = order.id
        await uow.commit()

    # Verify in new session
    async with session_factory() as session:
        repo_order = await session.get(Order, order_id)
        assert repo_order is not None
        assert repo_order.quote_id == "q1"
        assert repo_order.status == OrderStatus.NEW


@pytest.mark.asyncio
async def test_uow_quote_and_outbox(db_session, session_factory, clean_db):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    async with uow:
        uow.quotes.add(Quote(
            direction=QuoteDirection.ON_RAMP,
            pair="usd-usdt",
            amount_in=Decimal("100"),
            amount_out=Decimal("99"),
            fee_rate=Decimal("0.01"),
            provider_name="test_provider",
            valid_until=datetime.now() + timedelta(minutes=10),
        ))

        order = Order(
            incoming_amount=Decimal("100"),
            outgoing_amount=Decimal("98"),
            incoming_account="acct-1",
            outgoing_account="acct-2",
            direction=QuoteDirection.ON_RAMP,
            pair="USDT-USD",
            quote_id="q2",
            status=OrderStatus.COMPLETED,
        )
        uow.orders.add(order)
        await uow._session.flush()  # to get order.id

        uow.outbox.add(Outbox(
            order_id=order.id,
            event_type=OutboxEventType.ORDER_COMPLETED,
            payload={"amount_in": 100, "provider_name": "test_provider"},
        ))
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
