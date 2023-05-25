from typing import Any

import orjson as json
import pytest
from pydantic import ValidationError

from overlead.odm.fields.objectid_field import ObjectId
from overlead.odm.motor.model import ObjectIdModel
from overlead.odm.types import undefined


class ModelObjectId(ObjectIdModel):
    pass


def test_model_json() -> None:
    a = ModelObjectId()
    assert a.json() == json.dumps({}).decode()
    assert a.dict() == {}
    a = ModelObjectId(id=ObjectId())
    assert a.json() == json.dumps({"id": str(a.id)}).decode()
    assert a.dict() == {"id": a.id}


@pytest.mark.parametrize(
    "value",
    [None, 0, 123, True, False, "", "123", "undefined", str, ModelObjectId, ObjectId],
)
def test_model_objectid_bad_id(value: Any) -> None:
    with pytest.raises(ValidationError):
        ModelObjectId(id=value)


@pytest.mark.parametrize(
    "value",
    [None, 0, 123, True, False, "", "123", "undefined", str, ModelObjectId, ObjectId],
)
def test_model_objectid_bad_id_assign(value: Any) -> None:
    a = ModelObjectId(id=ObjectId())
    with pytest.raises(ValidationError):
        a.id = value


@pytest.mark.parametrize(
    "value",
    [ObjectId(), undefined, str(ObjectId())],
)
def test_model_objectid_ok_id(value: Any) -> None:
    a = ModelObjectId(id=value)
    assert a.id == ObjectId(value) if value is not undefined else value


@pytest.mark.parametrize(
    "value",
    [ObjectId(), undefined, str(ObjectId())],
)
def test_model_objectid_ok_id_assign(value: Any) -> None:
    a = ModelObjectId(id=ObjectId())
    assert a.id != ObjectId(value) if value is not undefined else value
    a.id = value
    assert a.id == ObjectId(value) if value is not undefined else value
