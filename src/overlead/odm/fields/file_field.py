import pickle
from collections.abc import Mapping
from datetime import datetime
from typing import IO, Any, Generic, Protocol, Self, TypeAlias, TypeVar, cast

import orjson
from motor.motor_asyncio import (
    AsyncIOMotorClientSession,
    AsyncIOMotorGridFSBucket,
    AsyncIOMotorGridOut,
)
from pydantic import ValidationError
from pydantic.fields import ModelField

from overlead.odm.fields.objectid_field import ObjectId, ObjectIdType
from overlead.odm.metamodel import BaseMeta

_FieldType = TypeVar("_FieldType")
_Session: TypeAlias = AsyncIOMotorClientSession
_T = TypeVar("_T")


class FileField(ObjectId):
    """Тип для работы с GridFS."""

    meta: BaseMeta
    field: ModelField

    def __init__(self, v: ObjectIdType, field: ModelField) -> None:
        super().__init__(v)
        self.field = field
        self.meta = field.model_config.overlead_meta  # type: ignore[attr-defined]

    @property
    def _gridfs(self) -> AsyncIOMotorGridFSBucket:
        return self.meta.gridfs

    async def __aenter__(self) -> AsyncIOMotorGridOut:
        return await self._gridfs.open_download_stream(self)

    async def __aexit__(
        self,
        type_: Any,  # pyright: ignore
        exc: Any,  # pyright: ignore
        traceback: Any,  # pyright: ignore
    ) -> None:
        ...

    async def read(self) -> bytes:
        """Прочитать файлик целиком."""
        async with self as stream:
            return await stream.read()

    async def write(
        self,
        filename: str,
        value: bytes | IO[Any],
        session: _Session | None = None,
    ) -> None:
        """Записать файлик."""
        async with self._gridfs.open_upload_stream_with_id(
            self,
            filename,
            session=session,
        ) as stream:
            await stream.write(value)

    async def delete(self, session: _Session | None = None) -> None:
        """Удалить файлик."""
        await self._gridfs.delete(self, session=session)

    @property
    async def aliases(self) -> list[str] | None:
        """Aliases."""
        async with self as stream:
            return stream.aliases

    @property
    async def chunk_size(self) -> int:
        """Chunk size."""
        async with self as stream:
            return stream.chunk_size

    @property
    async def content_type(self) -> str | None:
        """Content type."""
        async with self as stream:
            return stream.content_type

    @property
    async def filename(self) -> str | None:
        """Filename."""
        async with self as stream:
            return stream.filename

    @property
    async def length(self) -> int:
        """Length."""
        async with self as stream:
            return stream.length

    @property
    async def md5(self) -> Any:
        """Md5."""
        async with self as stream:
            return stream.md5

    @property
    async def metadata(self) -> Mapping[str, Any] | None:
        """Metadata."""
        async with self as stream:
            return stream.metadata

    @property
    async def name(self) -> str | None:
        """Name."""
        async with self as stream:
            return stream.name

    @property
    async def upload_date(self) -> datetime:
        """Upload date."""
        async with self as stream:
            return stream.upload_date

    @classmethod
    def __validate__(cls, v: ObjectIdType, field: ModelField) -> Self:
        v = super().__validate__(v, field)
        if not hasattr(field.model_config, "overlead_meta"):
            error = "invalid base model type"
            raise TypeError(error)
        return cls(v, field)


class DataFileCoder(Protocol, Generic[_T]):
    """Необходивые свойства сереализатора."""

    @staticmethod
    def loads(__obj: bytes) -> _T:
        """Сереализовать."""
        ...

    @staticmethod
    def dumps(__obj: _T) -> bytes:
        """Десереализовать."""
        ...


class DataFileField(FileField, Generic[_FieldType]):
    """Сериализация и десериализация данных и запись их в GridFS."""

    coder: DataFileCoder[_FieldType]

    async def load(self) -> _FieldType:
        """Получить данные и десерелизоватьk их."""
        assert self.field.sub_fields
        data = self.coder.loads(await self.read())
        value, error = self.field.sub_fields[0].validate(data, {}, loc=())
        if error:
            raise ValidationError([error], self.__class__)  # type: ignore[arg-type]
        return cast(_FieldType, value)

    async def dump(self, filename: str, value: _FieldType) -> None:
        """Серелизовать данные и записать."""
        data = self.coder.dumps(value)
        await self.write(filename, data)


class JsonFileField(DataFileField[_FieldType], Generic[_FieldType]):
    """JSON сериализация данных."""

    coder = orjson  # type: ignore[assignment]


class PickleFileField(DataFileField[_FieldType], Generic[_FieldType]):
    """Pickle сериализация данных."""

    coder = pickle  # type: ignore[assignment]
