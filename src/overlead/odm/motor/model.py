from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable
from typing import Any
from typing import Dict
from typing import Generic
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import overload

from pymongo.results import DeleteResult
from pymongo.results import InsertManyResult
from pymongo.results import InsertOneResult
from pymongo.results import UpdateResult

from overlead.odm.fields import ObjectId
from overlead.odm.model import BaseModel
from overlead.odm.types import Undefined
from overlead.odm.types import undefined

from .cursor import MotorCursor

__all__ = ['MotorModel', 'ObjectIdModel']

T = TypeVar('T')
V = TypeVar('V')
M = TypeVar('M', bound='MotorModel')


class MotorModel(BaseModel[T], Generic[T]):
    @overload
    async def save(self: M) -> M:
        ...

    async def save(self: MotorModel[T]) -> MotorModel[T]:
        olds = self._olds
        data = self._dump()

        if not self.is_created:
            result = await self.insert_one(data)
            self.id = result.inserted_id
            self._olds = data
            self._olds['_id'] = self.id
            return self

        keys = set(data) | set(olds)
        upds: Dict[str, Dict[str, Any]] = defaultdict(dict)

        for key in keys:
            new = data.get(key, undefined)
            old = olds.get(key, undefined)

            if new == old:
                continue

            if new is undefined:
                upds['$unset'][key] = ''

            else:
                upds['$set'][key] = new

        await self.update_one({'_id': self.id}, upds)
        self._olds = data
        return self

    @overload
    async def delete(self: M) -> M:
        ...

    async def delete(self: MotorModel[T]) -> MotorModel[T]:
        if not self.is_created:
            raise ValueError(f'object is not created\n{self}')

        await self.delete_one({'_id': self.id})
        return self

    @classmethod
    async def find_one(cls: Type[M], *args: Any, **kwargs: Any) -> Optional[M]:
        kwargs['limit'] = 1
        item = await cls.collection.find_one(*args, **kwargs)
        return cls._load(item) if item is not None else None

    @classmethod
    def find(cls: Type[M], *args: Any, **kwargs: Any) -> MotorCursor[M]:
        return MotorCursor(cls, cls.collection.find(*args, **kwargs))

    @classmethod
    def insert_one(cls, *args: Any, **kwargs: Any) -> Awaitable[InsertOneResult]:
        return cls.collection.insert_one(*args, **kwargs)

    @classmethod
    def update_one(cls, *args: Any, **kwargs: Any) -> Awaitable[UpdateResult]:
        return cls.collection.update_one(*args, **kwargs)

    @classmethod
    def delete_one(cls, *args: Any, **kwargs: Any) -> Awaitable[DeleteResult]:
        return cls.collection.delete_one(*args, **kwargs)

    @classmethod
    def insert_many(cls, *args: Any, **kwargs: Any) -> Awaitable[InsertManyResult]:
        return cls.collection.insert_many(*args, **kwargs)

    @classmethod
    def update_many(cls, *args: Any, **kwargs: Any) -> Awaitable[UpdateResult]:
        return cls.collection.update_many(*args, **kwargs)

    @classmethod
    def delete_many(cls, *args: Any, **kwargs: Any) -> Awaitable[DeleteResult]:
        return cls.collection.delete_many(*args, **kwargs)

    @classmethod
    def count_documents(cls, *args: Any, **kwargs: Any) -> Awaitable[int]:
        return cls.collection.count_documents(*args, **kwargs)

    @classmethod
    async def bulk_write():
        pass

    @classmethod
    async def aggregate():
        pass

    @classmethod
    async def ensure_indexes(cls) -> None:
        indexes = cls.__meta__.indexes
        for index in indexes:
            index = index.dict()
            keys, opts = index['keys'], index['opts']
            keys = list(keys.items())

            await cls.collection.create_index(keys, **opts)

    @classmethod
    async def ensure_all_indexes(cls) -> None:
        for collection in cls.__registry__:
            if issubclass(collection, cls):
                try:
                    collection.collection
                except ValueError:
                    continue

                print(f'{collection}: Ensure indexes')
                await collection.ensure_indexes()


class ObjectIdModel(MotorModel[ObjectId]):
    pass
