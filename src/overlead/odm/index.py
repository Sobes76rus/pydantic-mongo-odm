from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Literal, Self, Union, cast

from pydantic import BaseModel, constr

__all__ = ["Index"]

IndexKeysValues = Union[Literal[1], Literal[-1], Literal["text"], Literal["hashed"]]


class IndexTypeError(TypeError):
    """Неверный тип индекса."""

    def __init__(self, v: Any) -> None:
        super().__init__(f"{v}")


class IndexValueError(ValueError):
    """Неверное значение индекса."""

    def __init__(self, v: Any) -> None:
        super().__init__(f"{v}")


class IndexKeys(BaseModel):
    """Ключи индекса."""

    __root__: dict[  # type: ignore[valid-type]
        constr(min_length=1, strict=True, strip_whitespace=True),  # pyright: ignore
        IndexKeysValues,
    ]

    class Config:
        """Конфиг ключей."""

        allow_mutation = False
        extra = "forbid"

    @staticmethod
    def validate_item(v: Any) -> tuple[Any, Any]:
        """Валидация ключа."""
        if isinstance(v, str):
            regex = re.match(r"^([-+#@])?([\w_][\w\d_]*)", v)
            if not regex:
                raise IndexValueError(v)

            group = regex.group(1) or "+"
            value = {"+": 1, "-": -1, "#": "hashed", "@": "text"}[group]
            v = (regex.group(2), value)

        if isinstance(v, dict):
            v = list(v.items())
            if len(v) != 1:
                raise IndexValueError(v)
            v = v[0]  # pyright: ignore

        if not isinstance(v, tuple):
            raise IndexTypeError(v)

        if len(v) != 2:  # noqa: PLR2004
            raise IndexValueError(v)

        return cast(tuple[Any, Any], v)

    @classmethod
    def validate(cls, v: Any) -> Self:
        """Валидация списка ключей."""
        if isinstance(v, str):
            v = v.split(" ")

        if isinstance(v, list | tuple):
            v = [cls.validate_item(i) for i in v]

        if not isinstance(v, list | tuple | Mapping):
            raise IndexTypeError(v)

        if len(v) == 0:
            raise IndexValueError(v)

        item = super().validate(v)

        if len(item.__root__) != len(v):
            raise IndexValueError(v)

        return item


class IndexOpts(BaseModel):
    """Настройки индекса."""

    # session:
    name: str | None
    unique: bool | None
    background: bool | None
    sparse: bool | None
    bucket_size: int | None
    min: int | None
    max: int | None
    expire_after_seconds: int | None
    partial_filter_expression: Any
    # collation:
    wildcard_pattern: bool | None
    hidden: bool | None

    class Config:
        """Конфиг для настроек."""

        allow_mutation = False
        allow_population_by_field_value = True
        extra = "forbid"
        fields = {
            "bucket_size": "bucketSize",
            "expire_after_seconds": "expireAfterSeconds",
            "partial_filter_expression": "partialFilterExpression",
            "wildcard_pattern": "wildcardPattern",
        }

    def dict(self, **kwargs: Any) -> dict[str, Any]:
        """Преобразование в словарик."""
        kwargs["exclude_none"] = True
        return super().dict(**kwargs)


class Index(BaseModel):
    """Модель для индекса монги."""

    keys: IndexKeys
    opts: IndexOpts

    class Config:
        """Конфиг индекса."""

        allow_mutation = False
        extra = "forbid"

    @classmethod
    def parse_obj(cls, index: Any) -> Index:
        """Парсим обьект в ключик."""
        if isinstance(index, Index):
            return index

        if isinstance(index, str | list | dict):
            return Index(keys=index, opts={})  # type: ignore[arg-type]

        if isinstance(index, tuple) and len(index) == 2:  # noqa: PLR2004
            keys, opts = index
            return Index(keys=keys, opts=opts)

        return Index(keys="", opts={})  # type: ignore[arg-type]
