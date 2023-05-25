import asyncio
import inspect
from collections.abc import Generator
from typing import Any

import pytest
from testcontainers.compose import DockerCompose  # type: ignore[import]

from overlead.odm.client import get_client
from overlead.odm.motor.model import ObjectIdModel


def pytest_collection_modifyitems(
    session: Any,  # pyright: ignore # noqa: ARG001
    config: Any,  # pyright: ignore # noqa: ARG001
    items: Any,
) -> None:
    for item in items:
        if isinstance(item, pytest.Function) and inspect.iscoroutinefunction(
            item.function,
        ):
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture(autouse=True, scope="session")
def event_loop() -> Generator[Any, None, None]:
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
def _start_docker() -> Generator[None, None, None]:  # pyright: ignore
    with DockerCompose(".") as compose:
        host = compose.get_service_host("mongodb", 27017)
        port = compose.get_service_port("mongodb", 27017)
        port = int(port)

        ObjectIdModel.__meta__.client = get_client(
            host=host,
            port=port,
            connect=False,
            replicaSet="pytestRs",
        )
        ObjectIdModel.__meta__.database_name = "overlead-odm-test"

        yield


@pytest.fixture(autouse=True)
async def _clear_database() -> Any:  # pyright: ignore
    names = await ObjectIdModel.database.list_collection_names()
    for name in names:
        await ObjectIdModel.database.get_collection(name).delete_many({})
