import asyncio

import pytest

from overlead.odm.client import get_client
from overlead.odm.motor.model import ObjectIdModel


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
def motor_client(event_loop):
    return get_client(connect=False, motor=True)


@pytest.fixture
def motor_model(motor_client):
    class Model(ObjectIdModel):
        class Meta:
            client = motor_client
            database_name = 'overlead-odm-test'

    return Model


@pytest.fixture
def motor_model_A(motor_model):
    class Model(motor_model):
        class Meta:
            collection_name = 'collectionA'

    return Model


@pytest.fixture
def motor_model_B(motor_model):
    class Model(motor_model):
        class Meta:
            collection_name = 'collectionB'

    return Model
