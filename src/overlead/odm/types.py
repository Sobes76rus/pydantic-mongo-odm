from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    ParamSpec,
    Self,
    TypeAlias,
    TypeGuard,
    TypeVar,
)

import wrapt

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from pydantic.typing import CallableGenerator

__all__ = ["Undefined", "undefined"]


_TypeVar = TypeVar("_TypeVar")
_T = TypeVar("_T")
_R_co = TypeVar("_R_co", covariant=True)
_P = ParamSpec("_P")


class classproperty(  # noqa: N801
    wrapt.ObjectProxy,  # type: ignore[type-arg]
    Generic[_P, _R_co],
):
    """Декоратор для property методов класса."""

    def __init__(self, wrapped: Callable[_P, _R_co]) -> None:
        super().__init__(wrapped)

    def __get__(self, instance: _T | None, owner: type[_T]) -> _R_co:
        function: Callable[[], _R_co] = self.__wrapped__.__get__(instance, owner)
        return function()


class UndefinedType:
    """Предствление undefined значения."""

    def __repr__(self) -> str:
        return "OverleadUndefined"

    def __copy__(self) -> Self:
        return self

    def __reduce__(self) -> str:
        return "Undefined"

    def __deepcopy__(self, _: Any) -> Self:
        return self

    @classmethod
    def __get_validators__(cls) -> CallableGenerator:
        yield cls.__validate__

    @classmethod
    def __validate__(cls, v: Any) -> UndefinedType:
        if isnotundefined(v):
            error = "Not undefined"
            raise TypeError(error)

        assert isundefined(v)
        return v


undefined = UndefinedType()
Undefined: TypeAlias = UndefinedType | _TypeVar


def isundefined(value: object) -> TypeGuard[UndefinedType]:
    """Значение undefined."""
    return isinstance(value, UndefinedType)


def isnotundefined(value: Undefined[_TypeVar]) -> TypeGuard[_TypeVar]:
    """Значение не undefined."""
    return not isundefined(value)
