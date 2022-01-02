from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable
from typing import IO
from typing import Any
from typing import Dict
from typing import Generic
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union
from typing import overload

from motor.core import AgnosticClientSession
from pymongo import DeleteMany
from pymongo import DeleteOne
from pymongo import InsertOne
from pymongo import ReplaceOne
from pymongo import UpdateMany
from pymongo import UpdateOne
from pymongo.results import BulkWriteResult
from pymongo.results import DeleteResult
from pymongo.results import InsertManyResult
from pymongo.results import InsertOneResult
from pymongo.results import UpdateResult

from overlead.odm import triggers
from overlead.odm.fields import ObjectId
from overlead.odm.model import BaseModel
from overlead.odm.triggers import trigger
from overlead.odm.types import Undefined
from overlead.odm.types import UndefinedType
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
        await self.run_triggers(triggers.before_save)

        if not self.is_created:
            await self.run_triggers(triggers.before_create)

            data = self._dump()

            result = await self.insert_one(data)
            self.id = result.inserted_id
            self._olds = data
            self._olds['_id'] = self.id

            await self.run_triggers(triggers.after_create)
            await self.run_triggers(triggers.after_save, created=True)

            return self

        await self.run_triggers(triggers.before_update)

        olds = self._olds
        data = self._dump()

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

        if upds:
            await self.update_one({'_id': self.id}, upds)

        self._olds = data

        await self.run_triggers(triggers.after_update)
        await self.run_triggers(triggers.after_save, created=False)

        return self

    @overload
    async def delete(self: M) -> M:
        ...

    async def delete(self: MotorModel[T]) -> MotorModel[T]:
        if not self.is_created:
            raise ValueError(f'object is not created\n{self}')

        await self.run_triggers(triggers.before_delete)
        await self.delete_one({'_id': self.id})
        await self.run_triggers(triggers.after_delete)
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
    def insert_many(
        cls,
        documents: list,
        ordered: bool = True,
        bypass_document_validation: bool = False,
        session: Optional[AgnosticClientSession] = None,
    ) -> Awaitable[InsertManyResult]:
        return cls.collection.insert_many(
            documents=documents,
            ordered=ordered,
            bypass_document_validation=bypass_document_validation,
            session=session,
        )

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
    def bulk_write(
        cls,
        requests: list[Union[InsertOne, UpdateOne, UpdateMany, ReplaceOne, DeleteOne, DeleteMany]],
        *,
        ordered: bool = True,
        bypass_document_validation: bool = False,
        session: Optional[AgnosticClientSession] = None,
    ) -> Awaitable[BulkWriteResult]:
        return cls.collection.bulk_write(
            requests,
            ordered=ordered,
            bypass_document_validation=bypass_document_validation,
            session=session,
        )

    @classmethod
    def aggregate(cls, pipeline: list[dict[str, Any]], **kwargs: Any) -> Any:
        return cls.collection.aggregate(pipeline, **kwargs)

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

    async def run_triggers(self, type: Type[trigger], **kwargs):
        def wrapper(func):
            async def wrapt(*args, **kwargs):
                return asyncio.to_thread(func, *args, **kwargs)

            return wrapt

        for trig in self.get_triggers(type):

            if not asyncio.iscoroutinefunction(trig.func):
                trig.func = wrapper(trig.func)

            gen = trig.exec(self, **kwargs)
            for val in gen:
                while asyncio.iscoroutine(val):
                    val = await val

                try:
                    gen.send(val)
                except StopIteration:
                    pass

    @classmethod
    async def create_file(
        cls,
        filename: str,
        data: Undefined[Optional[Union[str, bytes, IO[Any]]]],
        id: Any = None,
    ) -> Optional[Undefined[ObjectId]]:
        if data is None:
            return data

        if data is undefined:
            return undefined

        id = id or ObjectId()
        stream = cls.gridfs.open_upload_stream_with_id(id, filename)
        await stream.write(data)
        return id


class ObjectIdModel(MotorModel[ObjectId]):
    pass
