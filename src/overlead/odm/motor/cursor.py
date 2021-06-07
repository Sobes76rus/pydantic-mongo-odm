from collections.abc import AsyncGenerator
from collections.abc import Awaitable
from typing import Any
from typing import AsyncIterable
from typing import AsyncIterator
from typing import Generic
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar

from motor.motor_asyncio import AsyncIOMotorCollection
from motor.motor_asyncio import AsyncIOMotorCursor

T = TypeVar('T')


class MotorCursor(Generic[T]):
    model: Type[T]
    cursor: AsyncIOMotorCursor

    def __init__(self, model: Type[T], cursor: AsyncIOMotorCursor) -> None:
        self.model = model
        self.cursor = cursor

    def __aiter__(self) -> AsyncIterator[T]:
        async def iterate() -> AsyncGenerator[T, None]:
            async for item in self.cursor:
                yield self.model._load(item)

        return iterate()

    async def to_list(self, length: Optional[int]) -> List[T]:
        items = await self.cursor.to_list(length=length)
        return [self.model._load(item) for item in items]
