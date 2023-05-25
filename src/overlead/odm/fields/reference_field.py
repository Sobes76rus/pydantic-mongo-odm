from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar, cast

from overlead.odm.fields.objectid_field import (
    ObjectId,
    ObjectIdDocumentIsNotCreatedError,
    ObjectIdType,
)
from overlead.odm.model import BaseModel

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Awaitable

    from pydantic.fields import ModelField

    from overlead.odm.motor.model import MotorModel

M = TypeVar("M", bound="MotorModel")  # type: ignore[type-arg]


class ReferenceModelTypeRequiredError(TypeError):
    """Модель не указана."""

    def __init__(self) -> None:
        super().__init__("Model required.")


class ReferenceModelTypeInvalidError(TypeError):
    """Неподходящая модель в ссылке."""

    def __init__(self, type_: Any) -> None:
        super().__init__(f"Invalid model: {type_}")


class ReferenceDocumentModelError(TypeError):
    """Неподходящая модель документа."""

    def __init__(self, v: Any, type_: Any) -> None:
        super().__init__(f"Invalid document model: {v}, should be {type_}")


class DeleteRule(str, enum.Enum):
    """Поведение при удалении зависимого документа."""

    NOTHING = "NOTHING"
    NULLIFY = "NULLIFY"
    CASCADE = "CASCADE"
    DENY = "DENY"


class Reference(ObjectId, Generic[M]):
    """Ссылка на документ."""

    type_: type[M]
    field: ModelField

    def __init__(self, v: ObjectIdType, type_: type[M], field: ModelField) -> None:
        super().__init__(v)

        if not issubclass(type_, BaseModel):
            raise ReferenceModelTypeInvalidError(type_)

        self.type_ = type_
        self.field = field

    @classmethod
    def __validate__(cls, v: Any, field: ModelField) -> Self:
        if not field.sub_fields:
            raise ReferenceModelTypeRequiredError

        type_ = field.sub_fields[0].type_
        if not issubclass(type_, BaseModel):
            raise ReferenceModelTypeInvalidError(type_)

        if isinstance(v, Reference):
            if v.type_ != type_:
                raise ReferenceModelTypeInvalidError(v.type_)

            return cast(Self, v)

        if isinstance(v, type_):
            if v.is_created:
                return cls(v.id, type_, field)  # pyright: ignore

            raise ObjectIdDocumentIsNotCreatedError(v)

        if isinstance(v, BaseModel):
            raise ReferenceDocumentModelError(v, type_)

        return cls(super().__validate__(v, field), type_, field)  # pyright: ignore

    def load(self) -> Awaitable[M | None]:
        """Загрузить документ."""
        return self.type_.find_one({"_id": self})

    def __getstate__(self) -> dict[str, Any]:  # type: ignore[override]
        state = self.__dict__.copy()
        state["_ObjectId__id"] = self._ObjectId__id
        if "field" in state:
            del state["field"]
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self._ObjectId__id = state.pop("_ObjectId__id")
        self.__dict__.update(state)
