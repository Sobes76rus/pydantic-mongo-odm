from collections.abc import MutableMapping
from typing import Any

from bson.codec_options import TypeRegistry
from bson.raw_bson import RawBSONDocument
from motor.motor_asyncio import AsyncIOMotorClient

__all__ = ["get_client"]


# @lru_cache(None)
def get_client(  # noqa: PLR0913
    host: str | list[str] | None = "localhost",
    port: int | None = 27017,
    document_class: type[RawBSONDocument]
    | type[MutableMapping[Any, Any]]
    | None = None,
    tz_aware: bool | None = None,
    connect: bool | None = None,
    type_registry: TypeRegistry | None = None,
    **kwargs: Any,
) -> AsyncIOMotorClient:
    """Создать клиент для монги."""
    return AsyncIOMotorClient(
        host=host,
        port=port,
        document_class=document_class,
        tz_aware=tz_aware,
        connect=connect,
        type_registry=type_registry,
        **kwargs,
    )
