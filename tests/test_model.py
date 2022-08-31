from typing import Any
from typing import Optional
from xml.dom import InvalidAccessErr

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import AnyHttpUrl
from pydantic import BaseModel as PydanticModel
from pymongo import MongoClient

from overlead.odm.client import get_client
from overlead.odm.model import BaseModel
from overlead.odm.types import Undefined
from overlead.odm.types import undefined


class ModelTest(BaseModel[Any]):
    value: Optional[str]

    class Meta:
        client = get_client(motor=True)
        database_name = 'test'
        collection_name = 'test'


@pytest.mark.parametrize('value', [
    get_client(motor=False),
    MongoClient(),
    AsyncIOMotorClient,
    123,
    '123',
])
def test_client_wrong_type(value):
    class TestModel(BaseModel):
        class Meta:
            client = value

    with pytest.raises(TypeError) as exc:
        TestModel.client

    assert 'AsyncIOMotorClient is required' in str(exc)


def test_client_correct_type():
    assert isinstance(ModelTest.client, AsyncIOMotorClient)


@pytest.mark.parametrize('value', [
    '123',
    '321',
    'test_overdrive',
    'test.overdrive',
])
def test_client_correct_database_name(value):
    class TestModel(BaseModel):
        class Meta:
            database_name = value

    assert TestModel.database_name == value


@pytest.mark.parametrize('value', [123, ModelTest, InvalidAccessErr, str])
def test_client_wrong_database_name(value):
    class TestModel(BaseModel):
        class Meta:
            database_name = value

    with pytest.raises(TypeError) as exc:
        TestModel.database_name

    assert 'str required' in str(exc)


def test_database_correct_type():
    assert isinstance(ModelTest.database, AsyncIOMotorDatabase)


def test_database_correct_name():
    assert ModelTest.database.name == ModelTest.database_name


def test_collection_correct_type():
    assert isinstance(ModelTest.collection, AsyncIOMotorCollection)


def test_collection_correct_name():
    assert ModelTest.collection.name == ModelTest.collection_name


@pytest.mark.parametrize('value, type_, msg', [
    (123, TypeError, 'str required'),
    (ModelTest, TypeError, 'str required'),
    (InvalidAccessErr, TypeError, 'str required'),
    (str, TypeError, 'str required'),
    (None, ValueError, 'collection name required'),
    ('', ValueError, 'collection name required'),
])
def test_client_wrong_collection_name(value, type_, msg):
    class TestModel(BaseModel):
        class Meta:
            collection_name = value

    with pytest.raises(type_) as exc:
        TestModel.collection_name

    assert msg in str(exc)


@pytest.mark.parametrize('value', ['123', '321', 'required', 'str.required'])
def test_client_correct_collection_name(value):
    class TestModel(BaseModel):
        class Meta:
            collection_name = value

    assert TestModel.collection_name == value


def test_any_http_url_with_undefined():
    class A(BaseModel):
        u: Undefined[AnyHttpUrl] = undefined

    class Form(PydanticModel):
        u: Optional[AnyHttpUrl]

    a = A(u='http://overlead.me')
    f = Form(u='http://overlead.me')
    assert type(f.u) == AnyHttpUrl
    A.u = f.u
