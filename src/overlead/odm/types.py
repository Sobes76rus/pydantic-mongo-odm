from __future__ import annotations

import enum
import typing
from typing import Any
from typing import Generic
from typing import Literal
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from pydantic import ValidationError
from pydantic.fields import ModelField
from pydantic.json import ENCODERS_BY_TYPE

from overlead.odm.fields.objectid_field import ObjectId

__all__ = ['Undefined', 'undefined']

UndefinedType = TypeVar('UndefinedType')
Und = TypeVar('Und', bound='UndefinedClass')


class UndefinedClass:
    singleton: Optional[UndefinedClass] = None

    def __new__(cls: Type[Und], *args: Any) -> Und:
        if not cls.singleton:
            singleton: Und = super().__new__(cls, *args)
            cls.singleton = singleton

        return cls.singleton

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    def __repr__(self):
        return 'undefined'

    def __str__(self):
        return 'undefined'

    def __bool__(self):
        return False

    @classmethod
    def validate(
        cls,
        v: Any,
    ) -> UndefinedClass:
        if v is undefined:
            return undefined

        raise ValueError(f'{v} is not undefined')

    @classmethod
    def __modify_schema__(self, field_schema):
        field_schema.update(
            type='string',
            examples=["undefined"],
        )


class UndefinedStrClass(UndefinedClass):
    @classmethod
    def validate(cls, v) -> UndefinedClass:
        if v == 'undefined':
            return undefined

        return super().validate(v)


class Error:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any):
        raise ValueError(v)


undefined = UndefinedClass()
Undefined = Union[UndefinedClass, UndefinedType]
UndefinedStr = Union[UndefinedStrClass, UndefinedClass, UndefinedType]

# undefined = UndefinedClassEnum.undefined

# assert UndefinedClassEnum[undefined.name] == undefined
# assert UndefinedClassEnum(undefined.value) == undefined
# Undefined = Union[Literal[UndefinedClassEnum], UndefinedType]

__all__ = ['Undefined', 'UndefinedStr', 'undefined', 'Error']
