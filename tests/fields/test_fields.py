from __future__ import annotations

import pickle
from typing import Any

import orjson as json
import pytest
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ValidationError

from overlead.odm.fields.objectid_field import (
    ObjectId,
    ObjectIdDocumentIsNotCreatedError,
    ObjectIdInvalidError,
    ObjectIdTypeError,
)
from overlead.odm.fields.reference_field import (
    Reference,
    ReferenceDocumentModelError,
    ReferenceModelTypeInvalidError,
    ReferenceModelTypeRequiredError,
)
from overlead.odm.motor.model import MotorModel as BaseModel
from overlead.odm.motor.model import ObjectIdModel as OIDModel


class ObjectIdModel(BaseModel[Any]):
    val: ObjectId


class ReferenceModel(BaseModel[Any]):
    value: Reference[ReferenceModel] | None = None


def test_objectid_correct_objectid() -> None:
    val = ObjectId()
    a = ObjectIdModel(val=val)
    assert a.val == val


def test_objectid_correct_str() -> None:
    val = str(ObjectId())
    a = ObjectIdModel(val=val)  # type: ignore[arg-type]
    assert a.val == ObjectId(val)


def test_objectid_wrong_str() -> None:
    val = "123"

    with pytest.raises(ValidationError) as exc:
        ObjectIdModel(val=val)  # type: ignore[arg-type]

    assert (
        exc.value.errors()[0]["type"].split(".")[-1]
        in ObjectIdInvalidError.__name__.lower()
    )


@pytest.mark.parametrize(
    ("value", "type_"),
    [
        (123, ObjectIdTypeError),
        (True, ObjectIdTypeError),
        (lambda: None, ObjectIdTypeError),
        (str, ObjectIdTypeError),
        (ObjectId, ObjectIdTypeError),
        (ObjectIdModel, ObjectIdTypeError),
    ],
)
def test_objectid_wrong_type(value: Any, type_: Any) -> None:
    with pytest.raises(ValidationError) as exc:
        ObjectIdModel(val=value)

    assert exc.value.errors()[0]["type"].split(".")[-1] in type_.__name__.lower()


def test_reference_no_generic() -> None:
    class ReferenceWrongGeneric(BaseModel[Any]):
        value: Reference  # type: ignore[type-arg]

    with pytest.raises(ValidationError) as exc:
        ReferenceWrongGeneric(value=ObjectId())  # type: ignore[arg-type]

    assert (
        exc.value.errors()[0]["type"].split(".")[-1]
        in ReferenceModelTypeRequiredError.__name__.lower()
    )


def test_reference_wrong_generic() -> None:
    class ReferenceWrongGeneric(BaseModel[Any]):
        value: Reference[int]  # type: ignore[type-var]

    with pytest.raises(ValidationError) as exc:
        ReferenceWrongGeneric(value=ObjectId())  # type: ignore[arg-type]

    assert (
        exc.value.errors()[0]["type"].split(".")[-1]
        in ReferenceModelTypeInvalidError.__name__.lower()
    )


@pytest.mark.parametrize(
    "value",
    [
        str(ObjectId()),
        ObjectId(),
        ReferenceModel(id=ObjectId()),
        Reference(ObjectId(), ReferenceModel, None),  # type: ignore[arg-type]
    ],
)
def test_reference_correct_values(value: Any) -> None:
    a = ReferenceModel(value=value)
    value = value.id if isinstance(value, BaseModel) else value
    assert a.value == ObjectId(value)
    assert isinstance(a.value, Reference)
    assert a.value.type_ == ReferenceModel


@pytest.mark.parametrize(
    ("value", "type_"),
    [
        (123, ObjectIdTypeError),
        ("123", ObjectIdInvalidError),
        (BaseModel(id=123), ReferenceDocumentModelError),
        (BaseModel(), ReferenceDocumentModelError),
        (ReferenceModel(), ObjectIdDocumentIsNotCreatedError),
        (
            Reference(ObjectId(), BaseModel, None),  # type: ignore[arg-type]
            ReferenceModelTypeInvalidError,
        ),
    ],
)
def test_reference_wrong_values(value: Any, type_: Any) -> None:
    with pytest.raises(ValidationError) as exc:
        ReferenceModel(value=value)

    assert exc.value.errors()[0]["type"].split(".")[-1] in type_.__name__.lower()


def test_reference_jsonable() -> None:
    model = ReferenceModel(value=ObjectId())  # type: ignore[arg-type]
    model.value = ObjectId()  # type: ignore[assignment]
    assert model.json() == json.dumps({"value": str(model.value)}).decode()


def test_reference_model() -> None:
    class Ref(PydanticBaseModel):
        ref: Reference[ReferenceModel]

    class RefOID(OIDModel):
        ref: Reference[RefOID]

    Ref(ref=ObjectId())  # type: ignore[arg-type]
    b = RefOID(id=ObjectId(), ref=ObjectId())  # type: ignore[arg-type]
    c = RefOID(ref=b)  # type: ignore[arg-type]

    assert c.ref == b.id


def test_reference_pickle() -> None:
    value = ObjectId()
    a = ReferenceModel(value=value)  # type: ignore[arg-type]
    ref = a.value

    assert isinstance(ref, Reference)
    assert ref.type_ == ReferenceModel
    assert ref == ref

    new = pickle.loads(pickle.dumps(ref))

    assert isinstance(new, Reference)
    assert new == ref
    assert new.type_ == ReferenceModel

    new = pickle.loads(pickle.dumps(new))

    assert isinstance(new, Reference)
    assert new == ref
    assert new.type_ == ReferenceModel
