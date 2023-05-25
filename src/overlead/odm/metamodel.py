from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, dataclass_transform

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pydantic.fields import Field, FieldInfo
from pydantic.main import BaseModel as PydanticModel
from pydantic.main import ModelMetaclass

from overlead.odm.errors import ModelInvalidIndexError
from overlead.odm.index import Index
from overlead.odm.triggers import trigger
from overlead.odm.types import classproperty

if TYPE_CHECKING:  # pragma: no cover
    from bson.codec_options import TypeCodec

    from overlead.odm.model import BaseModel

_T = TypeVar("_T")


class ModelTypeError(TypeError):
    """Если модель не является потомком pydantic.BaseModel."""

    def __init__(self) -> None:
        super().__init__("The model type must be a descendant of `pydantic.BaseModel`.")


def _inherit_meta(
    self_meta: type[BaseMeta] | None,
    parent_meta: type[BaseMeta],
    **namespace: Any,
) -> type[BaseMeta]:
    base_classes: tuple[type[BaseMeta], ...]
    match self_meta:
        case None:
            base_classes = (parent_meta,)
        case _:
            base_classes = (self_meta, parent_meta)

    indexes = getattr(self_meta, "indexes", ())
    if not isinstance(indexes, tuple):
        raise ModelInvalidIndexError(indexes)
    indexes = tuple(Index.parse_obj(o) for o in (*parent_meta.indexes, *indexes))

    triggers = getattr(self_meta, "triggers", ())
    triggers = tuple(trig for trig in (*parent_meta.triggers, *triggers))

    codecs = getattr(self_meta, "type_codecs", [])
    codecs = tuple(codec for codec in (*parent_meta.type_codecs, *codecs))

    namespace["indexes"] = indexes
    namespace["triggers"] = triggers
    namespace["type_codecs"] = codecs

    return type("Meta", base_classes, namespace)


class BaseMeta:
    """Base config for models."""

    client: AsyncIOMotorClient | None = None
    database_name: str | None = None
    collection_name: str | None = None

    indexes: tuple[Index, ...] = ()
    type_codecs: tuple[TypeCodec, ...] = ()
    triggers: tuple[trigger[Any, Any, Any], ...] = ()

    @classproperty
    @classmethod
    def gridfs(cls) -> AsyncIOMotorGridFSBucket:
        """Доступ к GridFS."""
        assert cls.client
        assert cls.database_name
        return AsyncIOMotorGridFSBucket(cls.client.get_database(cls.database_name))


@dataclass_transform(
    kw_only_default=True,
    field_descriptors=(Field, FieldInfo),  # type: ignore[literal-required]
)
class BaseModelMetaclass(ModelMetaclass):
    """Metaclass for models."""

    __BASE_MODEL_CLASSES__: ClassVar[list[type[BaseModel[Any]]]] = []
    __meta__: type[BaseMeta]
    __registry__: list[type[PydanticModel]]

    def __new__(  # noqa: D102
        cls,
        name: str,
        bases: tuple[type[BaseModel[_T]]],
        namespace: dict[str, Any],
        **kwds: Any,
    ) -> type[BaseModel[_T]]:
        base_cls = cls._get_base_class(bases)

        # Создаем новый мета класс для новой модели
        meta = BaseMeta
        pydantic = False

        for base in reversed(bases):
            if base_cls and issubclass(base, base_cls):
                meta = _inherit_meta(base.__meta__, meta)
            if issubclass(base, PydanticModel):
                pydantic = True

        if not pydantic:
            raise ModelTypeError

        meta_from_namespace = namespace.get("Meta")
        meta = _inherit_meta(meta_from_namespace, meta)

        # Регистрируем тригеры и удаляем функции из модели
        triggers = list(getattr(meta, "triggers", []))
        for key, val in list(namespace.items()):
            if isinstance(val, trigger):
                triggers.append(val)
                del namespace[key]
        meta.triggers = tuple(triggers)

        config = namespace.get("Config")
        if not config:
            config = type("Config", (object,), {})
        config.overlead_meta = meta  # type: ignore[union-attr]

        namespace["Config"] = config
        # Namespace для нового классаол
        namespace["__meta__"] = meta
        # namespace["__classes__"] = []
        # namespace["__triggers__"] = defaultdict(lambda: defaultdict(list))

        if not base_cls:
            namespace["__registry__"] = []

        new: type[BaseModel[_T]] = super().__new__(cls, name, bases, namespace, **kwds)
        new.update_forward_refs()
        new.__registry__.append(new)

        if not base_cls:
            BaseModelMetaclass.__BASE_MODEL_CLASSES__.append(new)

        return new

    @staticmethod
    def _get_base_class(
        bases: tuple[type[BaseModel[_T]]],
    ) -> type[BaseModel[_T]] | None:
        for base_cls in BaseModelMetaclass.__BASE_MODEL_CLASSES__:
            if any(issubclass(cls, base_cls) for cls in bases):
                return base_cls
        return None
