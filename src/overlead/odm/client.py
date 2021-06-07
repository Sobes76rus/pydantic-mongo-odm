from functools import lru_cache
from typing import Any
from typing import List
from typing import Literal
from typing import MutableMapping
from typing import Optional
from typing import Type
from typing import Union
from typing import overload

from bson.codec_options import TypeRegistry
from bson.raw_bson import RawBSONDocument
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

__all__ = ['get_client']


@overload
def get_client(
    host: Union[str, List[str], None] = ...,
    port: Optional[int] = ...,
    document_class: Union[Type[RawBSONDocument], Type[MutableMapping[Any, Any]], None] = ...,
    tz_aware: Optional[bool] = ...,
    connect: Optional[bool] = ...,
    type_registry: Optional[TypeRegistry] = ...,
    motor: Literal[True] = ...,
    **kwargs: Any,
) -> AsyncIOMotorClient:
    ...


@overload
def get_client(
    host: Union[str, List[str], None] = ...,
    port: Optional[int] = ...,
    document_class: Union[Type[RawBSONDocument], Type[MutableMapping[Any, Any]], None] = ...,
    tz_aware: Optional[bool] = ...,
    connect: Optional[bool] = ...,
    type_registry: Optional[TypeRegistry] = ...,
    motor: Literal[False] = ...,
    **kwargs: Any,
) -> MongoClient:
    ...


# @lru_cache(None)
def get_client(
    host: Union[str, List[str], None] = 'localhost',
    port: Optional[int] = 27017,
    document_class: Union[Type[RawBSONDocument], Type[MutableMapping[Any, Any]], None] = dict,
    tz_aware: Optional[bool] = False,
    connect: Optional[bool] = True,
    type_registry: Optional[TypeRegistry] = None,
    motor: bool = True,
    **kwargs: Any,
) -> Union[AsyncIOMotorClient, MongoClient]:

    if motor:
        return AsyncIOMotorClient(
            host=host,
            port=port,
            document_class=document_class,
            tz_aware=tz_aware,
            connect=connect,
            type_registry=type_registry,
            **kwargs,
        )

    else:
        return MongoClient(
            host=host,
            port=port,
            document_class=document_class,
            tz_aware=tz_aware,
            connect=connect,
            type_registry=type_registry,
            **kwargs,
        )
