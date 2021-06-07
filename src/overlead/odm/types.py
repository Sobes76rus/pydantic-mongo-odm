from __future__ import annotations

from typing import Any
from typing import Optional
from typing import TypeVar
from typing import Union

__all__ = ['Undefined', 'undefined']


class UndefinedType:
    singleton: Optional[UndefinedType] = None

    def __new__(cls, *args: Any) -> UndefinedType:
        if not UndefinedType.singleton:
            singleton: UndefinedType = super().__new__(cls, *args)
            UndefinedType.singleton = singleton

        return UndefinedType.singleton

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> UndefinedType:
        if v is not undefined:
            raise ValueError('')

        return v


UV = TypeVar('UV')
undefined = UndefinedType()
Undefined = Union[UndefinedType, UV]
