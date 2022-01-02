import asyncio
import inspect

import pytest
from testcontainers.compose import DockerCompose

from overlead.odm.client import get_client
from overlead.odm.motor.model import ObjectIdModel


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        if isinstance(item, pytest.Function) and inspect.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture(autouse=True, scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope='session')
def start_docker():
    with DockerCompose(".") as compose:
        host = compose.get_service_host('mongodb', 27017)
        port = compose.get_service_port('mongodb', 27017)
        port = port and int(port)

        ObjectIdModel.__meta__.client = get_client(host=host, port=port, connect=False, motor=True)
        ObjectIdModel.__meta__.database_name = 'overlead-odm-test'

        yield


@pytest.fixture(autouse=True, scope='function')
async def clear_database():
    names = await ObjectIdModel.database.list_collection_names()
    for name in names:
        await ObjectIdModel.database.get_collection(name).delete_many({})


@pytest.fixture
def motor_model_A(motor_model):
    class Model(ObjectIdModel):
        class Meta:
            collection_name = 'collectionA'

    return Model


@pytest.fixture
def motor_model_B(motor_model):
    class Model(ObjectIdModel):
        class Meta:
            collection_name = 'collectionB'

    return Model
