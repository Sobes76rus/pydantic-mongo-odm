from __future__ import annotations

import typing
from typing import Any
from typing import Generic
from typing import Literal
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from pydantic.fields import ModelField
from pydantic.json import ENCODERS_BY_TYPE

__all__ = ['Undefined', 'undefined']

UndefinedType = TypeVar('UndefinedType')
Und = TypeVar('Und', bound='Undefined')


class Undefined(Generic[UndefinedType]):
    singleton: Optional[Undefined[UndefinedType]] = None

    def __new__(cls: Type[Und], *args: Any) -> Und[UndefinedType]:
        if not cls.singleton:
            singleton: Undefined[UndefinedType] = super().__new__(cls, *args)
            cls.singleton = singleton

        return cls.singleton

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    def __repr__(self):
        return 'undefined'

    def __str__(self):
        return 'undefined'

    @classmethod
    def validate(
        cls,
        v: Union[Undefined[UndefinedType], UndefinedType],
        values: dict[str, Any],
        field: ModelField,
    ) -> Union[Undefined[UndefinedType], UndefinedType]:
        if not field.sub_fields:
            raise TypeError('required')

        if v is undefined:
            return undefined

        v, e = field.sub_fields[0].validate(v, values, loc='')

        if e:
            raise e.exc
        else:
            return v


class UndefinedStr(Undefined[UndefinedType], Generic[UndefinedType]):
    @classmethod
    def validate(
        cls,
        v: Union[Undefined[UndefinedType], UndefinedType, Literal['undefined']],
        values: dict[str, Any],
        field: ModelField,
    ) -> Union[Undefined[UndefinedType], UndefinedType]:
        if v == 'undefined':
            return undefined

        return super().validate(v, values, field)


class Error:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any):
        raise ValueError(v)


ENCODERS_BY_TYPE[Undefined] = str
ENCODERS_BY_TYPE[UndefinedStr] = str
undefined = UndefinedStr[Any]()
