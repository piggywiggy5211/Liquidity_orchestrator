from typing import Type, Optional, Sequence, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class LazyDtoSequence[DtoType](Sequence[DtoType]):
    def __init__(self, instances: Sequence[Any], dto_class: Type[DtoType]):
        self._instances = instances
        self._dto_class = dto_class

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self._dto_class.model_validate(inst) for inst in self._instances[index]]
        return self._dto_class.model_validate(self._instances[index])

    def __len__(self) -> int:
        return len(self._instances)

    def __iter__(self):
        for inst in self._instances:
            yield self._dto_class.model_validate(inst)


class BaseRepository[ModelType, DtoType]:
    def __init__(self, model: Type[ModelType], dto_class: Type[DtoType], session: AsyncSession):
        self.model = model
        self.dto_class = dto_class
        self.session = session

    async def get(self, id: int) -> tuple[ModelType | None, DtoType | None]:
        instance = await self.session.get(self.model, id)
        if instance:
            return instance, self.dto_class.model_validate(instance)
        return None, None

    async def get_all(self) -> tuple[Sequence[ModelType], Sequence[DtoType]]:
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        instances = result.scalars().all()
        return instances, LazyDtoSequence(instances, self.dto_class)

    def add(self, instance: ModelType) -> None:
        self.session.add(instance)

    async def delete(self, instance: ModelType) -> None:
        await self.session.delete(instance)
