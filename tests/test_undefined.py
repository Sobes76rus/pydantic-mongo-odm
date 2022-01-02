import pytest
from pydantic.error_wrappers import ValidationError

from overlead.odm.fields import ObjectId
from overlead.odm.fields import Reference
from overlead.odm.model import BaseModel
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


def test2():
    class A(BaseModel):
        a: Undefined[str] = '123'

    assert A().a == '123'
    assert A(a='321').a == '321'
    assert A(a='undefined').a == 'undefined'
    assert type(A(a='undefined').a) == str
    assert A(a=123).a == '123'
    assert A(a=undefined).a == undefined
    assert type(A(a=undefined).a) != str
    assert not isinstance(undefined, str)

    with pytest.raises(ValidationError):
        A(a=ObjectId())


def test3():
    class A(BaseModel):
        a: UndefinedStr[str] = 'undefined'

    assert A().a == undefined
    assert A(a='123').a == '123'
    assert A(a='undefined').a == undefined


def test4():
    class A(BaseModel):
        a: UndefinedStr[str] = ObjectId()

    with pytest.raises(ValidationError):
        A()
