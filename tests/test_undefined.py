from typing import Any

import pytest
from pydantic import validate_arguments

from overlead.odm.fields import ObjectId
from overlead.odm.types import Undefined, UndefinedType, undefined


def test_repr() -> None:
    assert repr(undefined) == "OverleadUndefined"


def test_str() -> None:
    assert str(undefined) == "OverleadUndefined"


@pytest.mark.parametrize(
    "value",
    [
        "undefined",
        "123",
        object,
        None,
        object(),
        ObjectId(),
        1,
        2,
        3,
        int,
        UndefinedType,
    ],
)
def test_validator(value: Any) -> None:
    @validate_arguments()
    def validate(val: Undefined[Any]) -> bool:
        assert val != undefined
        assert val == value
        return True

    assert validate(value)


@pytest.mark.parametrize(
    "value",
    [
        "undefined",
        "123",
        3,
    ],
)
def test_validator_str(value: Any) -> None:
    @validate_arguments()
    def validate(val: Undefined[str]) -> bool:
        assert val != undefined
        assert val == str(value)
        return True

    assert validate(value)
