from typing import Any

import pytest

from overlead.odm.errors import ModelInvalidIndexError
from overlead.odm.model import BaseModel


class ModelA(BaseModel[Any]):
    class Meta:
        indexes = (
            "a",
            "+b",
            "-a",
            ("a", {"unique": True}),
        )


def test_indexes_good() -> None:
    indexes = ModelA.__meta__.indexes
    indx = [i.dict() for i in indexes]
    assert indx == [
        {"keys": {"_id": 1}, "opts": {}},
        {"keys": {"a": 1}, "opts": {}},
        {"keys": {"b": 1}, "opts": {}},
        {"keys": {"a": -1}, "opts": {}},
        {"keys": {"a": 1}, "opts": {"unique": True}},
    ]


def test_indexes_bad() -> None:
    with pytest.raises(ModelInvalidIndexError):

        class ModelBad(BaseModel[Any]):  # pyright: ignore
            class Meta:
                indexes = "a"
