import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from liquidity_orchestrator.database.uow import UnitOfWorkSqlAlchemy
from liquidity_orchestrator.domain.enums import (
    OrderStatus,
    OutboxEventType,
    QuoteDirection,
)
from liquidity_orchestrator.domain.models import Order, Outbox, Quote
from liquidity_orchestrator.integrations.providers import PROVIDERS_MAP
from liquidity_orchestrator.service.liquidity_service import LiquidityService
from sqlalchemy import select


@pytest.mark.asyncio
async def test_context_session_isolation(db_session, session_factory):
    """
    Test that uow.switch_session_context_for_task provides a new session and restores the original one.
    """
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP)

    main_session_id = id(uow._session)

    async def get_session_id():
        return id(uow._session)

    task_session_id = await service.uow.switch_session_context_for_task(get_session_id)

    # Verify task session is different from main session
    assert task_session_id != main_session_id

    # Verify main session is restored
    assert id(uow._session) == main_session_id


@pytest.mark.asyncio
async def test_parallel_context_sessions(db_session, session_factory):
    """
    Test that multiple tasks running in parallel have their own unique sessions.
    """
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP)

    async def delayed_session_id():
        s_id = id(uow._session)
        # Sleep to ensure overlap in execution
        await asyncio.sleep(0.05)
        # Verify session is still the same after sleep (no leakage from other tasks)
        assert id(uow._session) == s_id
        return s_id

    # Run 5 tasks in parallel
    results = await asyncio.gather(*[service.uow.switch_session_context_for_task(delayed_session_id) for _ in range(5)])

    # All session IDs must be unique
    assert len(set(results)) == 5
    # None of them should be the original session
    assert all(sid != id(db_session) for sid in results)


@pytest.mark.asyncio
async def test_nested_context_sessions(db_session, session_factory):
    """
    Test that nested uow.switch_session_context_for_task (if ever used) would handle context correctly.
    """
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, PROVIDERS_MAP)

    main_session_id = id(uow._session)

    async def inner_task():
        return id(uow._session)

    async def outer_task():
        outer_id = id(uow._session)
        inner_id = await service.uow.switch_session_context_for_task(inner_task)
        assert inner_id != outer_id
        assert id(uow._session) == outer_id
        return outer_id

    outer_session_id = await service.uow.switch_session_context_for_task(outer_task)

    assert outer_session_id != main_session_id
    assert id(uow._session) == main_session_id


@pytest.mark.asyncio
async def test_uow_order_creation(db_session, session_factory):
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
async def test_uow_quote_and_outbox(db_session, session_factory):
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    async with uow:
        uow.quotes.add(
            Quote(
                direction=QuoteDirection.ON_RAMP,
                pair="usd-usdt",
                amount_in=Decimal("100"),
                amount_out=Decimal("99"),
                fee_rate=Decimal("0.01"),
                provider_name="test_provider",
                valid_until=datetime.now() + timedelta(minutes=10),
            )
        )

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

        uow.outbox.add(
            Outbox(
                order_id=order.id,
                event_type=OutboxEventType.ORDER_COMPLETED,
                payload={"amount_in": 100, "provider_name": "test_provider"},
            )
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
