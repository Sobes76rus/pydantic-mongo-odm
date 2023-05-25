from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Generic,
    ParamSpec,
    Self,
    TypeAlias,
    TypeVar,
)

from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorGridFSBucket

from overlead.odm import triggers
from overlead.odm.errors import ModelNotCreatedError
from overlead.odm.fields import ObjectId
from overlead.odm.model import BaseModel
from overlead.odm.types import (
    Undefined,
    classproperty,
    isnotundefined,
    isundefined,
    undefined,
)

from .cursor import MotorCursor

if TYPE_CHECKING:
    from collections.abc import Awaitable, Sequence

    from motor.core import AgnosticClientSession
    from pymongo import (
        DeleteMany,
        DeleteOne,
        InsertOne,
        ReplaceOne,
        UpdateMany,
        UpdateOne,
    )
    from pymongo.results import (
        BulkWriteResult,
        DeleteResult,
        InsertManyResult,
        InsertOneResult,
        UpdateResult,
    )

    from overlead.odm.triggers import trigger


__all__ = ["MotorModel", "ObjectIdModel"]

_IdType = TypeVar("_IdType", covariant=True)
_P = ParamSpec("_P")
_DocumentType: TypeAlias = dict[str, Any]
_MotorModelType: TypeAlias = BaseModel[_IdType]

logger = logging.getLogger()


class MotorModel(_MotorModelType[_IdType], Generic[_IdType]):
    """Base class for MongoDB models."""

    async def save(self) -> Self:
        """Save model."""
        await self.run_triggers(triggers.before_save)

        if not self.is_created:
            await self.run_triggers(triggers.before_create)

            data = self._dump()

            result = await self.insert_one(data)
            self.id = result.inserted_id
            self._olds = data
            self._olds["_id"] = self.id

            await self.run_triggers(triggers.after_create)
            await self.run_triggers(
                triggers.after_save,
                created=True,  # pyright: ignore
            )

            return self

        await self.run_triggers(triggers.before_update)

        olds = self._olds
        data = self._dump()

        keys = set(data) | set(olds)
        upds: dict[str, dict[str, Any]] = defaultdict(dict)

        for key in keys:
            new = data.get(key, undefined)
            old = olds.get(key, undefined)

            if new == old:
                continue

            if new is undefined:
                upds["$unset"][key] = ""

            else:
                upds["$set"][key] = new

        if upds:
            await self.update_one({"_id": self.id}, upds)

        self._olds = data

        await self.run_triggers(triggers.after_update)
        await self.run_triggers(
            triggers.after_save,
            created=False,  # pyright: ignore
        )

        return self

    async def delete(self) -> Self:
        """Delete model."""
        if not self.is_created:
            raise ModelNotCreatedError(self)

        await self.run_triggers(triggers.before_delete)
        await self.delete_one({"_id": self.id})
        await self.run_triggers(triggers.after_delete)
        return self

    @classmethod
    async def find_one(cls, *args: Any, **kwargs: Any) -> Self | None:
        """Find one document."""
        kwargs["limit"] = 1
        item = await cls.collection.find_one(*args, **kwargs)
        return cls._load(item) if item is not None else None

    @classmethod
    def find(
        cls,
        filter: dict[str, Any],  # noqa: A002
        *args: Any,
        **kwargs: Any,
    ) -> MotorCursor[Self]:
        """Fine many documents."""
        # filter.setdefault('_cls', cls.__name__)
        return MotorCursor(cls, cls.collection.find(filter, *args, **kwargs))

    @classmethod
    def insert_one(cls, *args: Any, **kwargs: Any) -> Awaitable[InsertOneResult]:
        """Insert one document."""
        return cls.collection.insert_one(*args, **kwargs)

    @classmethod
    def update_one(cls, *args: Any, **kwargs: Any) -> Awaitable[UpdateResult]:
        """Update one document."""
        return cls.collection.update_one(*args, **kwargs)

    @classmethod
    def delete_one(cls, *args: Any, **kwargs: Any) -> Awaitable[DeleteResult]:
        """Delete one document."""
        return cls.collection.delete_one(*args, **kwargs)

    @classmethod
    def insert_many(
        cls,
        documents: list[Any],
        ordered: bool = True,
        bypass_document_validation: bool = False,
        session: AgnosticClientSession | None = None,
    ) -> Awaitable[InsertManyResult]:
        """Insert many documents."""
        documents = [
            doc._dump() if isinstance(doc, MotorModel) else doc  # noqa: SLF001
            for doc in documents
        ]

        return cls.collection.insert_many(
            documents=documents,
            ordered=ordered,
            bypass_document_validation=bypass_document_validation,
            session=session,
        )

    @classmethod
    def update_many(cls, *args: Any, **kwargs: Any) -> Awaitable[UpdateResult]:
        """Update many documents."""
        return cls.collection.update_many(*args, **kwargs)

    @classmethod
    def delete_many(cls, *args: Any, **kwargs: Any) -> Awaitable[DeleteResult]:
        """Delete many documents."""
        return cls.collection.delete_many(*args, **kwargs)

    @classmethod
    def count_documents(cls, *args: Any, **kwargs: Any) -> Awaitable[int]:
        """Count documents."""
        return cls.collection.count_documents(*args, **kwargs)

    @classmethod
    def bulk_write(
        cls,
        requests: Sequence[
            InsertOne[_DocumentType]
            | UpdateOne
            | UpdateMany
            | ReplaceOne[_DocumentType]
            | DeleteOne
            | DeleteMany
        ],
        *,
        ordered: bool = True,
        bypass_document_validation: bool = False,
        session: AgnosticClientSession | None = None,
    ) -> Awaitable[BulkWriteResult]:
        """Bluk write."""
        return cls.collection.bulk_write(
            requests,
            ordered=ordered,
            bypass_document_validation=bypass_document_validation,
            session=session,
        )

    @classmethod
    def aggregate(cls, pipeline: list[dict[str, Any]], **kwargs: Any) -> Any:
        """Aggregate."""
        return cls.collection.aggregate(pipeline, **kwargs)

    @classmethod
    async def ensure_indexes(
        cls,
        session: AsyncIOMotorClientSession | None = None,
    ) -> None:
        """Ensure all indexes in collections created."""
        logger.info("%s: Ensure indexes", cls)
        indexes = cls.__meta__.indexes
        for index in indexes:
            index_vals = index.dict()
            keys, opts = index_vals["keys"], index_vals["opts"]
            keys = list(keys.items())

            # if cls.__meta__.cls_constraint:
            #     opts['partialFilterExpression'] = {
            #         **cls.__meta__.partial_filter_expression,
            #         **opts.get('partialFilterExpression', {}),
            #     }

            await cls.collection.create_index(keys, **opts, session=session)

    @classmethod
    async def ensure_all_indexes(cls) -> None:
        """Ensure all indexes in all collections created."""
        for collection in cls.__registry__:
            if issubclass(collection, cls):
                await collection.ensure_indexes()

    async def run_triggers(
        self,
        type_: type[trigger[Self, _P, Any]],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None:
        """Execute triggers."""
        for trig in self._get_triggers(type_):
            for value in trig._exec(self, *args, **kwargs):  # noqa: SLF001
                while asyncio.iscoroutine(value):
                    value = await value  # noqa: PLW2901

    @classproperty
    @classmethod
    def gridfs(cls) -> AsyncIOMotorGridFSBucket:
        """Access to GridFS."""
        return AsyncIOMotorGridFSBucket(cls.database)

    @classmethod
    async def upload_file(
        cls,
        filename: str,
        data: Undefined[str | bytes | IO[Any] | None],
        metadata: dict[str, Any] | None = None,
        id: ObjectId | None = None,  # noqa: A002
    ) -> Undefined[ObjectId] | None:
        """Upload file to GridFS."""
        if data is None:
            return None

        if isundefined(data):
            return undefined

        assert isnotundefined(data)

        if isinstance(data, str):
            data = data.encode()

        id = id or ObjectId()  # noqa: A001
        await cls.gridfs.upload_from_stream_with_id(
            id,
            filename,
            data,
            metadata=metadata,
        )
        return id


_ObjectIdModelType: TypeAlias = MotorModel[ObjectId]


class ObjectIdModel(_ObjectIdModelType):
    """Model with `ObjectId` type of `id` attribute."""
