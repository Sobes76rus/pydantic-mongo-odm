import pytest
from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from overlead.odm.fields import ObjectId
from overlead.odm.fields import Reference
from overlead.odm.motor.model import ObjectIdModel
from overlead.odm.types import Undefined
from overlead.odm.types import UndefinedStr
from overlead.odm.types import undefined


def test():
    class B(ObjectIdModel):
        pass

    class A(BaseModel):
        s: Undefined[str] = undefined
        o: Undefined[ObjectId] = undefined
        r: Undefined[Reference[B]] = undefined
        l: Undefined[list[int]] = undefined
        u: UndefinedStr[str] = undefined

    oid = ObjectId()

    assert A(s='123').s == '123'
    assert A(o=oid).o == oid
    assert A(r=oid).r == oid
    assert A(l=[1, 2, 3]).l == [1, 2, 3]

    with pytest.raises(ValidationError) as exc:
        A(r=123)

    assert 'invalid objectid' in str(exc.value)
    assert '(type=type_error)' in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        A(s=ObjectId())

    assert '(type=type_error.str)' in str(exc.value)
