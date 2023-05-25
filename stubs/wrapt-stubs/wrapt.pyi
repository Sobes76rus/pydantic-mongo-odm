from collections.abc import Callable
from typing import Any, Generic, TypeVar

_F = TypeVar("_F", bound=Callable[..., Any])
_T = TypeVar("_T", bound=Any)

def decorator(
    wrapper: _F,
    enabled: bool | None = None,
    adapter: Callable[..., Any] | None = None,
) -> _F: ...

class ObjectProxy(Generic[_T]):
    __wrapped__: _T

    def __init__(self, wrapped: _T) -> None: ...
