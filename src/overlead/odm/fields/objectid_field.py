from typing import TYPE_CHECKING, Any, Self, TypeAlias, cast

from bson import ObjectId as BSONObjectId
from bson.errors import InvalidId
from pydantic.fields import ModelField

from overlead.odm.model import BaseModel

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.typing import CallableGenerator

ObjectIdType: TypeAlias = BSONObjectId | str


class ObjectIdTypeError(TypeError):
    """Некорректный тип `ObjectId`."""

    def __init__(self, v: Any) -> None:
        super().__init__(f"Invalid `ObjectId` type: {v}")


class ObjectIdInvalidError(ValueError):
    """Некорректное значение `ObjectId`."""

    def __init__(self, v: Any) -> None:
        super().__init__(f"Invalid `ObjectId` value: {v}")


class ObjectIdDocumentIsNotCreatedError(ValueError):
    """Документ еще не создан."""

    def __init__(self, doc: Any) -> None:
        super().__init__(f"Document is not created: {doc}")


class ObjectId(BSONObjectId):
    """Замена `bson.ObjectId`."""

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.__validate__

    @classmethod
    def __validate__(cls, v: Any, field: ModelField) -> Self:  # pyright: ignore
        if isinstance(v, str):
            try:
                v = ObjectId(v)
            except InvalidId as exc:
                raise ObjectIdInvalidError(v) from exc

        if isinstance(v, BaseModel):
            if not v.is_created:
                raise ObjectIdDocumentIsNotCreatedError(v)
            v = v.id

        if not isinstance(v, BSONObjectId):
            raise ObjectIdTypeError(v)

        if not isinstance(v, ObjectId):
            v = ObjectId(v)

        return cast(Self, v)

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        field_schema.update(
            type="string",
            examples=["5eb7cf5a86d9755df3a6c593", "5eb7cfb05e32e07750a1756a"],
        )
