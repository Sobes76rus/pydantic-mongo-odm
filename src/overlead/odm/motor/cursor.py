from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncGenerator, AsyncIterator

    from motor.motor_asyncio import AsyncIOMotorCursor

    from overlead.odm.motor.model import MotorModel

T = TypeVar("T", bound="MotorModel")  # type: ignore[type-arg]


class MotorCursor(Generic[T]):
    """Motor cursor."""

    model: type[T]
    cursor: AsyncIOMotorCursor

    def __init__(self, model: type[T], cursor: AsyncIOMotorCursor) -> None:
        self.model = model
        self.cursor = cursor

    def __aiter__(self) -> AsyncIterator[T]:
        async def iterate() -> AsyncGenerator[T, None]:
            async for item in self.cursor:
                yield self.model._load(item)  # noqa: SLF001

        return iterate()

    async def to_list(self, length: int | None) -> list[T]:
        """To list."""
        items = await self.cursor.to_list(length=length)
        return [self.model._load(item) for item in items]  # noqa: SLF001
