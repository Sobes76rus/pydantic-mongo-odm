from __future__ import annotations

import re
from typing import Any
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import constr
from pydantic.dataclasses import dataclass

__all__ = ['Index']

IndexKeysValues = Union[Literal[1], Literal[-1], Literal['text'], Literal['hashed']]


class IndexKeys(BaseModel):
    __root__: dict[constr(min_length=1, strict=True, strip_whitespace=True), IndexKeysValues]

    @staticmethod
    def validate_item(v):
        if isinstance(v, str):
            regex = re.match(r'^([-+#@])?([\w_][\w\d_]*)', v)
            if not regex:
                raise ValueError(f'invalid key: {v}')

            group = regex.group(1) or '+'
            value = {'+': 1, '-': -1, '#': 'hashed', '@': 'text'}[group]
            v = (regex.group(2), value)

        if isinstance(v, dict):
            v = list(v.items())
            if len(v) != 1:
                raise ValueError(f'invalid key: {v}')
            v = v[0]

        if not isinstance(v, tuple) or len(v) != 2:
            raise ValueError(f'invalid key: {v}')

        return v

    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            v = v.split(' ')

        if isinstance(v, list):
            v = [cls.validate_item(i) for i in v]

        return super().validate(v)


class IndexOpts(BaseModel):
    # session:
    name: Optional[str]
    unique: Optional[bool]
    background: Optional[bool]
    sparse: Optional[bool]
    bucketSize: Optional[int]
    min: Optional[int]
    max: Optional[int]
    expireAfterSeconds: Optional[int]
    partialFilterExpression: Optional[Any]
    # collation:
    wildcardPattern: Optional[bool]
    hidden: Optional[bool]

    def dict(self, **kwargs):
        kwargs['exclude_none'] = True
        return super().dict(**kwargs)


class Index(BaseModel):
    keys: IndexKeys
    opts: IndexOpts

    class Config:
        allow_mutation = False

    @classmethod
    def parse_obj(cls, index) -> Index:
        if isinstance(index, Index):
            return index

        if isinstance(index, (str, list, dict)):
            return Index(keys=index, opts={})

        if isinstance(index, tuple):
            keys, opts = index
            return Index(keys=keys, opts=opts)

        return super().parse_obj(index)
