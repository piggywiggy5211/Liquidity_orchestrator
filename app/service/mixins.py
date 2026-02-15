from typing import Callable, Any

class TaskWrapperMixin:
    async def task_wrapper(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        async with self.uow.session_factory() as session:
            token = self.uow.ctx_session.set(session)
            try:
                return await func(*args, **kwargs)
            finally:
                self.uow.ctx_session.reset(token)
