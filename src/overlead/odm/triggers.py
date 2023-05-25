from collections.abc import Awaitable, Callable, Generator
from typing import Concatenate, Generic, ParamSpec, Self, TypeAlias, TypeVar

from mypy_extensions import Arg
from pydantic import BaseModel

P = ParamSpec("P")
C = TypeVar("C")
A = TypeVar("A", bound=BaseModel)
R_co = TypeVar("R_co", covariant=True)
MbAwaitable: TypeAlias = Awaitable[C] | C


class trigger(Generic[A, P, R_co]):  # noqa: N801
    """base trigger class."""

    def __init__(self, reference_field: str | None = None) -> None:
        self.reference = reference_field

    def __call__(
        self,
        func: Callable[Concatenate[A, P], MbAwaitable[R_co]]
        | Callable[P, MbAwaitable[R_co]],
    ) -> Self:
        """Set trigger callback function."""
        self.func = func
        return self

    def _exec(
        self,
        instance: A,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Generator[MbAwaitable[R_co], None, None]:
        """Call callback."""
        function = self.func.__get__(instance)
        yield function(*args, **kwargs)


class before_save(trigger[A, [], None]):  # noqa: N801
    """trigger before method `save`."""


class after_save(trigger[A, [Arg(bool, "created")], None]):  # noqa: N801
    """trigger after method `save`."""


class before_create(trigger[A, [], None]):  # noqa: N801
    """trigger before method `save` if creating."""


class after_create(trigger[A, [], None]):  # noqa: N801
    """trigger after method `save` if created."""


class before_update(trigger[A, [], None]):  # noqa: N801
    """trigger before method `save` if updating."""


class after_update(trigger[A, [], None]):  # noqa: N801
    """trigger after method `save` if updated."""


class before_delete(trigger[A, [], None]):  # noqa: N801
    """trigger before method `delete`."""


class after_delete(trigger[A, [], None]):  # noqa: N801
    """trigger after method `delete`."""
