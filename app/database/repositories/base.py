from typing import Type, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.base import Base


class BaseRepository[ModelType: Base]:
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: int) -> Optional[ModelType]:
        return await self.session.get(self.model, id)

    async def get_all(self) -> Sequence[ModelType]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        await self.session.delete(instance)
