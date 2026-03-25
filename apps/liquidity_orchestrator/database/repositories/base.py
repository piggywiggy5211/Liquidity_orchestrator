from typing import Any, Optional, Sequence, Type

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[ModelType]:
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, record_id: int) -> Optional[ModelType]:
        return await self.session.get(self.model, record_id)

    async def get_all(self) -> Sequence[ModelType]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def add(self, instance: ModelType) -> None:
        self.session.add(instance)

    async def update(self, record_id: int, **kwargs: Any) -> None:
        stmt = (
            update(self.model)
            .where(self.model.id == record_id)  # type: ignore[attr-defined]
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)

    async def delete(self, instance: ModelType) -> None:
        await self.session.delete(instance)
