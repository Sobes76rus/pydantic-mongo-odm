from typing import Any

import pytest
from pydantic import ValidationError

from overlead.odm.index import Index


@pytest.mark.parametrize(
    ("index", "expect"),
    [
        ("_id", ({"_id": 1}, {})),
        ("+key", ({"key": 1}, {})),
        ("-key", ({"key": -1}, {})),
        ("@key", ({"key": "text"}, {})),
        ("#key", ({"key": "hashed"}, {})),
        ("-a +b #c @d", ({"a": -1, "b": 1, "c": "hashed", "d": "text"}, {})),
        (["a", "b", "c"], ({"a": 1, "b": 1, "c": 1}, {})),
        ({"a": 1, "b": 1, "c": 1}, ({"a": 1, "b": 1, "c": 1}, {})),
        (
            [("a", -1), ("b", 1), ("c", "hashed")],
            ({"a": -1, "b": 1, "c": "hashed"}, {}),
        ),
        ([("a", 1)], ({"a": 1}, {})),
        (("-a", {"unique": True}), ({"a": -1}, {"unique": True})),
        ([{"a": 1}], ({"a": 1}, {})),
    ],
)
def test_index(index: Any, expect: Any) -> None:
    index = Index.parse_obj(index)
    index = index.dict()

    assert index["keys"] == expect[0]
    assert index["opts"] == expect[1]


@pytest.mark.parametrize(
    "index",
    [
        {"key": 2},
        {"key": -2},
        {"key": "asf"},
        {"key": "hashedd"},
        "!key",
        str,
        None,
        int,
        "",
        {"": 1},
        ({}, {"unique": True}),
        ({"key": 1}, {"unique": "error"}),
        ((("a", 1), ("b", 1)),),
        ((("a", 1), ("b", 1)), {"index": 1}, ()),
        ("a", {"index2": True}),
        {1: 1},
        1,
        (1, 1),
        [1, 1],
        ["+a", "-a"],
        ("a", {"index": "True"}),
        [{"a": 1, "b": 1}],
    ],
)
def test_index_error(index: Any) -> None:
    with pytest.raises((ValidationError, TypeError)):
        assert not Index.parse_obj(index)
