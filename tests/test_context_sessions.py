import asyncio
import pytest
from unittest.mock import AsyncMock
from app.database.uow import UnitOfWorkSqlAlchemy
from app.service.liquidity_service import LiquidityService

@pytest.mark.asyncio
async def test_context_session_isolation(db_session, session_factory):
    """
    Test that task_wrapper provides a new session and restores the original one.
    """
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, AsyncMock())

    main_session_id = id(uow._session)
    
    async def get_session_id():
        return id(uow._session)

    # Execute via task_wrapper
    task_session_id = await service.task_wrapper(get_session_id)

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
    service = LiquidityService(uow, AsyncMock())

    async def delayed_session_id():
        s_id = id(uow._session)
        # Sleep to ensure overlap in execution
        await asyncio.sleep(0.05)
        # Verify session is still the same after sleep (no leakage from other tasks)
        assert id(uow._session) == s_id
        return s_id

    # Run 5 tasks in parallel
    results = await asyncio.gather(*[
        service.task_wrapper(delayed_session_id) for _ in range(5)
    ])

    # All session IDs must be unique
    assert len(set(results)) == 5
    # None of them should be the original session
    assert all(sid != id(db_session) for sid in results)

@pytest.mark.asyncio
async def test_nested_context_sessions(db_session, session_factory):
    """
    Test that nested task_wrappers (if ever used) would handle context correctly.
    """
    uow = UnitOfWorkSqlAlchemy(session_factory, db_session)
    service = LiquidityService(uow, AsyncMock())

    main_session_id = id(uow._session)

    async def inner_task():
        return id(uow._session)

    async def outer_task():
        outer_id = id(uow._session)
        inner_id = await service.task_wrapper(inner_task)
        assert inner_id != outer_id
        assert id(uow._session) == outer_id
        return outer_id

    outer_session_id = await service.task_wrapper(outer_task)
    
    assert outer_session_id != main_session_id
    assert id(uow._session) == main_session_id
