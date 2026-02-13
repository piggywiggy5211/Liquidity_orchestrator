from typing import Type, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[ModelType]:
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: int) -> Optional[ModelType]:
        return await self.session.get(self.model, id)

    async def get_all(self) -> Sequence[ModelType]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def add(self, instance: ModelType) -> None:
        self.session.add(instance)

    async def delete(self, instance: ModelType) -> None:
        await self.session.delete(instance)
