from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Generic
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import Field
from pydantic import PrivateAttr
from pydantic.generics import GenericModel as PydanticModel
from pydantic.main import ModelMetaclass
from pydantic.typing import is_namedtuple
from pydantic.utils import sequence_like

from overlead.odm.types import Undefined
from overlead.odm.types import undefined

if TYPE_CHECKING:

    MetaType = Type['BaseMeta']

DictStrAny = Dict[str, Any]

ModelIdType = TypeVar('ModelIDType')
T = TypeVar('T')
M = TypeVar('M', bound='BaseModel')


def inherit_meta(self_meta: 'MetaType', parent_meta: 'MetaType', **namespace: Any) -> 'MetaType':
    if not self_meta:
        base_classes: Tuple['MetaType', ...] = (parent_meta, )

    elif self_meta == parent_meta:
        base_classes = (self_meta, )

    else:
        base_classes = self_meta, parent_meta

    namespace['indexes'] = tuple({
        *getattr(parent_meta, 'indexes', []),
        *getattr(self_meta, 'indexes', []),
    })

    return type('Meta', base_classes, namespace)


class BaseMeta:
    indexes: Tuple[Any, ...] = ()
    client: Optional[AsyncIOMotorClient] = None
    database_name: Optional[str] = None
    collection_name: Optional[str] = None


class BaseModelMetaclass(ModelMetaclass):
    def __new__(cls, name, bases, namespace: DictStrAny, **kwds):
        meta = BaseMeta

        for base in reversed(bases):
            if _is_base_document_class_defined and issubclass(base, BaseModel):
                meta = inherit_meta(base.__meta__, meta)

        meta_from_namespace = namespace.get('Meta')
        meta = inherit_meta(meta_from_namespace, meta)

        namespace['__meta__'] = meta

        new = super().__new__(cls, name, bases, namespace, **kwds)

        if _is_base_document_class_defined:
            pass

        new.update_forward_refs()

        return new


_is_base_document_class_defined = False


class BaseModel(PydanticModel, Generic[ModelIdType], metaclass=BaseModelMetaclass):
    if TYPE_CHECKING:
        __meta__: Type[BaseMeta]

    _refs = defaultdict(lambda: defaultdict(set))
    _olds: DictStrAny = PrivateAttr({})

    id: Undefined[ModelIdType] = Field(undefined, alias='_id')

    class Meta:
        indexes = ('_id', )

    class Config:
        validate_assignment = True

    @property
    def is_created(self) -> bool:
        return self.id is not undefined and self.id is not None

    def dict(self, **kwargs: Any) -> DictStrAny:
        kwargs.setdefault('by_alias', True)
        return super().dict(**kwargs)

    def _dump(self) -> DictStrAny:
        def del_undefined(v: T) -> T:
            if isinstance(v, dict):
                return {k: del_undefined(v) for k, v in v.items() if v is not undefined}  # type: ignore

            if sequence_like(v):
                seq = (del_undefined(val) for val in v if val is not undefined)  # type: ignore
                return v.__class__(*seq) if is_namedtuple(v.__class__) else v.__class__(seq)

            return v

        return del_undefined(self.dict())

    @classmethod
    def _load(cls: Type[M], data: DictStrAny) -> M:
        doc = cls(**data)
        doc._olds = data
        return doc

    if TYPE_CHECKING:
        client: AsyncIOMotorClient
        database: AsyncIOMotorDatabase
        collection: AsyncIOMotorCollection

        collection_name: str
        database_name: str

    else:

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
            return cls.database.get_collection(cls.collection_name)


_is_base_document_class_defined = True
