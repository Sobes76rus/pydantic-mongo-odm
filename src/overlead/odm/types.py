from __future__ import annotations

import typing
from typing import Any
from typing import Generic
from typing import Optional
from typing import TypeVar
from typing import Union

from pydantic.fields import ModelField
from pydantic.json import ENCODERS_BY_TYPE

__all__ = ['Undefined', 'undefined']

UndefinedType = TypeVar('UndefinedType')


class Undefined(Generic[UndefinedType]):
    singleton: Optional[Undefined[UndefinedType]] = None

    def __new__(cls, *args: Any) -> Undefined[UndefinedType]:
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
        field: ModelField,
    ) -> Union[Undefined[UndefinedType], UndefinedType]:
        if not field.sub_fields:
            raise TypeError('required')

        type_ = field.sub_fields[0].type_

        if v is undefined:
            return undefined

        if type_ is typing.Any:
            return v

        if isinstance(v, type_):
            return v

        return type_(v)


ENCODERS_BY_TYPE[Undefined] = str
undefined = Undefined[Any]()
