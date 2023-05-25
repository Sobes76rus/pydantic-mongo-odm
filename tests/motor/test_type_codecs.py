from typing import TYPE_CHECKING, Any, Self

from bson.codec_options import TypeEncoder, TypeRegistry

from overlead.odm.motor.model import ObjectIdModel
from overlead.odm.types import classproperty

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.typing import CallableGenerator


class Custom:
    def __init__(self, v: str) -> None:
        self.v = v

    @classmethod
    def __get_validators__(cls) -> "CallableGenerator":
        yield cls.__validate__

    @classmethod
    def __validate__(cls, v: Any) -> Self:
        if isinstance(v, cls):
            return v

        return cls(v)


class CustomEncoder(TypeEncoder):
    python_type = Custom  # pyright: ignore

    def transform_python(self, value: Any) -> Any:
        return value.v


class A(ObjectIdModel):
    a: Custom

    class Meta:
        collection_name = "A"
        type_codecs = (CustomEncoder(),)

    @classproperty
    @classmethod
    def _type_registry(cls) -> TypeRegistry:  # type: ignore[override]
        return TypeRegistry(type_codecs=[CustomEncoder()])


class B(ObjectIdModel):
    a: Custom

    class Meta:
        collection_name = "B"


async def test_custom_encoder() -> None:
    a = await A(a=Custom("123")).save()
    b = await A.find_one()
    assert b
    assert a.a.v == b.a.v


async def test_fallback_pickle_encoder() -> None:
    a = await B(a=Custom("123")).save()
    b = await B.find_one()
    assert b
    assert a.a.v == b.a.v
