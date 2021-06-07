import pytest

from overlead.odm.fields.objectid_field import ObjectId
from overlead.odm.motor.model import ObjectIdModel
from overlead.odm.types import undefined


class ModelObjectId(ObjectIdModel):
    pass


@pytest.mark.parametrize(
    'value',
    [None, 0, 123, True, False, '', '123', 'undefined', str, ModelObjectId, ObjectId],
)
def test_model_objectid_bad_id(value):
    with pytest.raises(Exception):
        ModelObjectId(_id=value)


@pytest.mark.parametrize(
    'value',
    [None, 0, 123, True, False, '', '123', 'undefined', str, ModelObjectId, ObjectId],
)
def test_model_objectid_bad_id_assign(value):
    a = ModelObjectId(_id=ObjectId())
    with pytest.raises(Exception):
        a.id = value


@pytest.mark.parametrize(
    'value',
    [ObjectId(), undefined, str(ObjectId())],
)
def test_model_objectid_ok_id(value):
    a = ModelObjectId(_id=value)
    assert a.id == ObjectId(value) if value is not undefined else value


@pytest.mark.parametrize(
    'value',
    [ObjectId(), undefined, str(ObjectId())],
)
def test_model_objectid_ok_id_assign(value):
    a = ModelObjectId(_id=ObjectId())
    assert a.id != ObjectId(value) if value is not undefined else value
    a.id = value
    assert a.id == ObjectId(value) if value is not undefined else value
