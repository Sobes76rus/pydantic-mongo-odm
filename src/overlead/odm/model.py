from __future__ import annotations

import inspect
import pickle
from collections import defaultdict
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import Generic
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar

import orjson
from bson.binary import USER_DEFINED_SUBTYPE
from bson.binary import Binary
from bson.codec_options import CodecOptions
from bson.codec_options import TypeCodec
from bson.codec_options import TypeDecoder
from bson.codec_options import TypeRegistry
from motor.core import AgnosticClient
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection
from motor.motor_asyncio import AsyncIOMotorDatabase
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from pydantic import PrivateAttr
from pydantic.fields import Field
from pydantic.fields import FieldInfo
from pydantic.generics import GenericModel as PydanticModel
from pydantic.main import ModelMetaclass
from pydantic.typing import is_namedtuple
from pydantic.utils import sequence_like
from typing_extensions import dataclass_transform

from overlead.odm.triggers import trigger
from overlead.odm.types import Undefined
from overlead.odm.types import undefined

from .index import Index

if TYPE_CHECKING:
    MetaType = Type['BaseMeta']

DictStrAny = dict[str, Any]
ModelIdType = TypeVar('ModelIdType')
T = TypeVar('T')
M = TypeVar('M', bound='BaseModel')


def inherit_meta(self_meta: 'MetaType', parent_meta: 'MetaType', **namespace: Any) -> 'MetaType':
    if not self_meta:
        base_classes: Tuple['MetaType', ...] = (parent_meta, )

    elif self_meta == parent_meta:
        base_classes = (self_meta, )

    else:
        base_classes = self_meta, parent_meta

    indexes = getattr(self_meta, 'indexes', [])
    if not isinstance(indexes, (tuple, list)):
        raise TypeError(f'indexes: {indexes}')

    namespace['indexes'] = tuple(
        Index.parse_obj(o) for o in (
            *getattr(parent_meta, 'indexes', []),
            *getattr(self_meta, 'indexes', []),
        ))

    triggers = getattr(self_meta, 'triggers', [])
    if not isinstance(triggers, (tuple, list)):
        raise TypeError(f'{triggers=}')

    namespace['triggers'] = tuple(trig for trig in (
        *getattr(parent_meta, 'triggers', []),
        *getattr(self_meta, 'triggers', []),
    ))

    codecs = getattr(self_meta, 'type_codecs', [])
    if not isinstance(codecs, (tuple, list)):
        raise TypeError(f'{triggers=}')

    namespace['type_codecs'] = tuple(codec for codec in (
        *getattr(parent_meta, 'type_codecs', []),
        *getattr(self_meta, 'type_codecs', []),
    ))

    return type('Meta', base_classes, namespace)


class BaseMeta:
    indexes: tuple[Index, ...] = ()
    client: Optional[AgnosticClient] = None
    database_name: Optional[str] = None
    collection_name: Optional[str] = None
    triggers: tuple[trigger, ...] = ()
    type_codecs: tuple[TypeCodec, ...] = ()


@dataclass_transform(kw_only_default=True, field_descriptors=(Field, FieldInfo))
class BaseModelMetaclass(ModelMetaclass):
    def __new__(cls, name, bases, namespace: DictStrAny, **kwds):
        meta = BaseMeta

        for base in reversed(bases):
            if _is_base_document_class_defined and issubclass(base, BaseModel):
                meta = inherit_meta(base.__meta__, meta)

        meta_from_namespace = namespace.get('Meta')
        meta = inherit_meta(meta_from_namespace, meta)

        triggers = list(getattr(meta, 'triggers', []))
        for key, val in list(namespace.items()):
            if isinstance(val, trigger):
                triggers.append(val)
                del namespace[key]
        setattr(meta, 'triggers', tuple(triggers))

        namespace['__meta__'] = meta

        if namespace.get('Config'):
            setattr(namespace.get('Config'), 'gridfs', lambda: new.gridfs)
        else:
            new_type = type('Config', (type, ), {'gridfs': lambda: new.gridfs})
            namespace['Config'] = new_type

        namespace['__classes__'] = []

        new = super().__new__(cls, name, bases, namespace, **kwds)

        if _is_base_document_class_defined:
            pass

        new.update_forward_refs()

        return new


_is_base_document_class_defined = False


def exclude_values(v: T, value) -> T:
    if isinstance(v, dict):
        return {k: exclude_values(v, value) for k, v in v.items() if v != value}  # type: ignore

    if sequence_like(v):
        seq = (exclude_values(val, value) for val in v if val != value)  # type: ignore
        return v.__class__(*seq) if is_namedtuple(v.__class__) else v.__class__(seq)

    return v


def exclude_undefined_values(v: T) -> T:
    return exclude_values(v, undefined)


def exclude_none_values(v: T) -> T:
    return exclude_values(v, None)


def json_dumps(v, *, default, exclude_undefined=True):
    if exclude_undefined:
        v = exclude_undefined_values(v)

    return orjson.dumps(v, default=default).decode()


def fallback_pickle_encoder(value):
    return Binary(pickle.dumps(value), USER_DEFINED_SUBTYPE)


class PickledBinaryDecoder(TypeDecoder):
    bson_type = Binary

    def transform_bson(self, value: Any) -> Any:
        if value.subtype == USER_DEFINED_SUBTYPE:
            return pickle.loads(value)
        return value


class BaseModel(PydanticModel, Generic[ModelIdType], metaclass=BaseModelMetaclass):
    if TYPE_CHECKING:
        __triggers__: ClassVar[dict[Type[BaseModel[ModelIdType]], dict[Type[trigger], list[trigger]]]]
        __meta__: ClassVar[Type[BaseMeta]]
        __registry__: ClassVar[list[Type[BaseModel[ModelIdType]]]]
        __classes__: ClassVar[list[str]]

        _olds: DictStrAny = PrivateAttr({})

    else:
        __triggers__: ClassVar[
            dict[
                Type[BaseModel[ModelIdType]],
                dict[Type[trigger], list[trigger]]
            ]
        ] = defaultdict(lambda: defaultdict(list))  # yapf: disable
        __registry__: ClassVar[
            list[Type[BaseModel[ModelIdType]]]
        ] = []  # yapf: disable
        __classes__: ClassVar[list[str]] = []
        _olds = PrivateAttr({})

    id: Undefined[ModelIdType] = undefined

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.__registry__.append(cls)

        for trig in cls.__meta__.triggers:
            bases = inspect.getmro(trig.__class__)
            for base in bases:
                if issubclass(base, trigger):
                    cls.__triggers__[cls][base].append(trig)

        if cls.__meta__.collection_name:
            coll_name = cls.__meta__.collection_name
            for klass in cls.__registry__:
                if klass.__meta__.collection_name == coll_name:
                    if issubclass(cls, klass):
                        klass.__classes__.append(cls.__name__)

    class Meta:
        indexes = ('_id', )
        type_codecs = (PickledBinaryDecoder(), )

    class Config:
        validate_assignment = True
        validate_all = True
        fields = {'id': '_id'}
        json_dumps = json_dumps

    @property
    def is_created(self) -> bool:
        return self.id is not undefined and self.id is not None

    def dict(self, **kwargs: Any) -> DictStrAny:
        # kwargs.setdefault('by_alias', True)
        exclude_undefined = kwargs.pop('exclude_undefined', True)
        values = super().dict(**kwargs)

        if exclude_undefined:
            values = exclude_undefined_values(values)

        return values

    def json(self, **kwargs: Any) -> str:
        kwargs.setdefault('exclude_undefined', True)
        return super().json(**kwargs)

    def _dump(self) -> DictStrAny:
        return self.dict(
            exclude_undefined=True,
            exclude=None,
            include=None,
            exclude_defaults=False,
            exclude_none=False,
            exclude_unset=False,
            by_alias=True,
        )

    @classmethod
    def _load(cls: Type[M], data: DictStrAny) -> M:
        doc = cls(**data)
        doc._olds = data
        return doc

    @classmethod
    @property
    def client(cls) -> AsyncIOMotorClient:
        if not cls.__meta__.client:
            raise ValueError('client required')

        if not isinstance(cls.__meta__.client, AsyncIOMotorClient):
            raise TypeError('AsyncIOMotorClient is required')

        return cls.__meta__.client

    @classmethod
    @property
    def database_name(cls) -> str:
        if not cls.__meta__.database_name:
            raise ValueError('database name is required')

        if not isinstance(cls.__meta__.database_name, str):
            raise TypeError('str required')

        return cls.__meta__.database_name

    @classmethod
    @property
    def collection_name(cls) -> str:
        if not cls.__meta__.collection_name:
            raise ValueError('collection name required')

        if not isinstance(cls.__meta__.collection_name, str):
            raise TypeError('str required')

        return cls.__meta__.collection_name

    @classmethod
    @property
    def database(cls) -> AsyncIOMotorDatabase:
        return cls.client.get_database(cls.database_name)

    @classmethod
    @property
    def collection(cls) -> AsyncIOMotorCollection:
        return cls.database.get_collection(cls.collection_name, codec_options=cls._codec_options)

    @classmethod
    @property
    def gridfs(cls) -> AsyncIOMotorGridFSBucket:
        return AsyncIOMotorGridFSBucket(cls.database)

    @classmethod
    @property
    def _codec_options(cls) -> CodecOptions:
        return CodecOptions(type_registry=cls._type_registry)

    @classmethod
    @property
    def _type_registry(cls) -> TypeRegistry:
        return TypeRegistry(
            type_codecs=cls.__meta__.type_codecs,
            fallback_encoder=fallback_pickle_encoder,
        )

    @classmethod
    def get_triggers(cls, type: Type[trigger]) -> list[trigger]:
        return cls.__triggers__[cls][type]


_is_base_document_class_defined = True
