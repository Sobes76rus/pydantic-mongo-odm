from __future__ import annotations

import json
from typing import Optional

import pytest
from pydantic import ValidationError

from overlead.odm.fields.objectid_field import ObjectId
from overlead.odm.fields.reference_field import Reference
from overlead.odm.model import BaseModel


class ObjectIdModel(BaseModel):
    val: ObjectId


class ReferenceModel(BaseModel):
    value: Optional[Reference[ReferenceModel]]


def test_objectid_correct_objectid():
    val = ObjectId()
    a = ObjectIdModel(val=val)
    a.val == val


def test_objectid_correct_str():
    val = str(ObjectId())
    a = ObjectIdModel(val=val)
    a.val == val


def test_objectid_wrong_str():
    val = '123'

    with pytest.raises(ValidationError) as exc:
        ObjectIdModel(val=val)

    assert 'invalid objectid' in str(exc.value)
    assert '(type=value_error)' in str(exc.value)


@pytest.mark.parametrize('value', [
    123,
    True,
    lambda: None,
    str,
    ObjectId,
    ObjectIdModel,
])
def test_objectid_wrong_type(value):
    with pytest.raises(ValidationError) as exc:
        ObjectIdModel(val=value)

    assert 'invalid objectid' in str(exc.value)
    assert '(type=type_error)' in str(exc.value)


def test_reference_no_generic():
    class ReferenceWrongGeneric(BaseModel):
        value: Reference

    with pytest.raises(ValidationError) as exc:
        ReferenceWrongGeneric(value=ObjectId())

    assert 'required' in str(exc.value)
    assert '(type=type_error)' in str(exc.value)


def test_reference_wrong_generic():
    class ReferenceWrongGeneric(BaseModel):
        value: Reference[int]

    with pytest.raises(ValidationError) as exc:
        ReferenceWrongGeneric(value=ObjectId())

    assert 'invalid reference' in str(exc.value)
    assert '(type=type_error)' in str(exc.value)


@pytest.mark.parametrize('value', [
    str(ObjectId()),
    ObjectId(),
    ReferenceModel(_id=ObjectId()),
    Reference(ObjectId(), ReferenceModel, None),
])
def test_reference_correct_values(value):
    a = ReferenceModel(value=value)
    value = value.id if isinstance(value, BaseModel) else value
    assert a.value == ObjectId(value)
    assert isinstance(a.value, Reference)
    assert a.value.type_ == ReferenceModel


@pytest.mark.parametrize('value, error, type_', [
    (123, 'invalid objectid', 'type_error'),
    ('123', 'invalid objectid', 'value_error'),
    (BaseModel(_id=ObjectId()), 'invalid objectid', 'type_error'),
    (BaseModel(), 'invalid objectid', 'type_error'),
    (ReferenceModel(), 'document is not created', 'value_error'),
    (Reference(ObjectId(), BaseModel, None), 'invalid reference', 'type_error'),
])
def test_reference_wrong_values(value, error, type_):
    with pytest.raises(ValidationError) as exc:
        ReferenceModel(value=value)

    assert error in str(exc.value)
    assert f'(type={type_})' in str(exc.value)


def test_reference_jsonable():
    model = ReferenceModel(value=ObjectId())
    assert model.json() == json.dumps({'value': str(model.value)})
