from typing import Any

import bson
from bson.codec_options import TypeEncoder
from bson.codec_options import TypeRegistry

from overlead.odm.motor.model import ObjectIdModel


class Custom:
    def __init__(self, v):
        self.v = v

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        if not isinstance(v, str):
            raise TypeError(v)

        return cls(v)


class CustomEncoder(TypeEncoder):
    python_type = Custom

    def transform_python(self, value: Any) -> Any:
        return value.v


class A(ObjectIdModel):
    a: Custom

    class Meta:
        collection_name = 'A'
        type_codecs = (CustomEncoder(), )

    @classmethod
    @property
    def _type_registry(cls) -> TypeRegistry:
        return TypeRegistry(type_codecs=[CustomEncoder()])


class B(ObjectIdModel):
    a: Custom

    class Meta:
        collection_name = 'B'


async def test_custom_encoder():
    a = await A(a=Custom('123')).save()
    b = await A.find_one()
    assert a.a.v == b.a.v


async def test_fallback_pickle_encoder():
    a = await B(a=Custom('123')).save()
    b = await B.find_one()
    assert a.a.v == b.a.v
