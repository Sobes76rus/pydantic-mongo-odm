from __future__ import annotations

from collections.abc import Mapping  # noqa: TCH003
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    ParamSpec,
    Self,
    TypeVar,
)

import orjson
from bson.codec_options import CodecOptions, TypeRegistry
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pydantic.fields import PrivateAttr
from pydantic.generics import GenericModel as PydanticModel

from overlead.odm.errors import (
    ModelClientError,
    ModelCollectionNameError,
    ModelDatabaseNameError,
)
from overlead.odm.metamodel import BaseModelMetaclass
from overlead.odm.types import Undefined, classproperty, undefined
from overlead.odm.utils import (
    PickledBinaryDecoder,
    exclude_undefined_values,
    fallback_pickle_encoder,
    json_dumps,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny

    from overlead.odm.triggers import trigger

_ModelIdType = TypeVar("_ModelIdType", covariant=True)

T = TypeVar("T", bound=PydanticModel)
P = ParamSpec("P")
R = TypeVar("R")


class BaseModel(PydanticModel, Generic[_ModelIdType], metaclass=BaseModelMetaclass):
    """Base model for collections."""

    _olds: Mapping[str, Any] = PrivateAttr({})
    id: Undefined[_ModelIdType] = undefined

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

    class Meta:
        """Base settings for collections."""

        indexes = ("_id",)
        type_codecs = (PickledBinaryDecoder(),)

    class Config:
        """Base pydantic settings for models."""

        validate_assignment = True
        validate_all = True
        fields = {"id": "_id"}
        json_dumps = json_dumps
        json_loads = orjson.loads
        allow_population_by_field_name = True

    @property
    def is_created(self) -> bool:
        """Check if model created."""
        return self.id is not undefined and self.id is not None

    def dict(
        self,
        *,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        exclude_undefined: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a dictionary representation of the model.

        Optionally specifying which fields to include or exclude.
        """
        values = super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

        if exclude_undefined:
            values = exclude_undefined_values(values)

        return values  # noqa: RET504

    def json(
        self,
        *,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        exclude_undefined: bool = True,
        encoder: Callable[[Any], Any] | None = None,
        models_as_dict: bool = True,
        **dumps_kwargs: Any,
    ) -> str:
        """
        Generate a JSON representation of the model.

        `include` and `exclude` arguments as per `dict()`.
        `encoder` is an optional function to supply as `default` to json.dumps(),
        other arguments as per `json.dumps()`.
        """
        return super().json(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            exclude_undefined=exclude_undefined,
            encoder=encoder,
            models_as_dict=models_as_dict,
            **dumps_kwargs,
        )

    def _dump(self) -> Dict[str, Any]:  # noqa: UP006
        return self.dict(
            exclude=None,
            include=None,
            exclude_undefined=True,
            exclude_defaults=False,
            exclude_none=False,
            exclude_unset=False,
            by_alias=True,
        )

    @classmethod
    def _load(cls, data: Mapping[str, Any]) -> Self:
        doc = cls(**data)
        doc._olds = data  # noqa: SLF001
        return doc

    @classproperty
    @classmethod
    def client(cls) -> AsyncIOMotorClient:
        """Mongo client."""
        if not cls.__meta__.client:
            raise ModelClientError

        if not isinstance(cls.__meta__.client, AsyncIOMotorClient):
            raise ModelClientError

        return cls.__meta__.client

    @classproperty
    @classmethod
    def database_name(cls) -> str:
        """Mongo database name."""
        if not cls.__meta__.database_name:
            raise ModelDatabaseNameError

        if not isinstance(cls.__meta__.database_name, str):
            raise ModelDatabaseNameError

        return cls.__meta__.database_name

    @classproperty
    @classmethod
    def collection_name(cls) -> str:
        """Mongo collection name."""
        if not cls.__meta__.collection_name:
            raise ModelCollectionNameError

        if not isinstance(cls.__meta__.collection_name, str):
            raise ModelCollectionNameError

        return cls.__meta__.collection_name

    @classproperty
    @classmethod
    def database(cls) -> AsyncIOMotorDatabase:
        """Motor database."""
        return cls.client.get_database(cls.database_name)

    @classproperty
    @classmethod
    def collection(cls) -> AsyncIOMotorCollection:
        """Motor collection."""
        return cls.database.get_collection(
            cls.collection_name,
            codec_options=cls._codec_options,
        )

    @classproperty
    @classmethod
    def _codec_options(cls) -> CodecOptions[Any]:
        return CodecOptions(type_registry=cls._type_registry)

    @classproperty
    @classmethod
    def _type_registry(cls) -> TypeRegistry:
        return TypeRegistry(
            type_codecs=cls.__meta__.type_codecs,
            fallback_encoder=fallback_pickle_encoder,
        )

    @classmethod
    def _get_triggers(
        cls,
        type_: type[trigger[T, P, R]],
    ) -> Generator[trigger[T, P, R], None, None]:
        for tr in cls.__meta__.triggers:
            if isinstance(tr, type_):
                yield tr
