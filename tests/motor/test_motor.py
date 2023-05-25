from random import randint
from typing import Any

import pytest
from pymongo import InsertOne

from overlead.odm import triggers
from overlead.odm.errors import ModelNotCreatedError
from overlead.odm.motor.model import ObjectIdModel
from overlead.odm.types import Undefined, isnotundefined, undefined


class Motor(ObjectIdModel):
    value: int

    class Meta:
        collection_name = "motor"
        indexes = (
            "value",
            {"value": "hashed"},
            ("-value", {"unique": True}),
            ["_id", "value"],
        )


class MotorUnd(Motor):
    value: Undefined[int] = undefined  # type: ignore[assignment]


@pytest.fixture(autouse=True, scope="module")
async def _create_collection() -> None:  # pyright: ignore
    await Motor.database.create_collection(Motor.collection_name)


async def test_ensure_indexes() -> None:
    await Motor.collection.drop_indexes()
    assert len(await Motor.collection.list_indexes().to_list(None)) == 1
    await Motor.ensure_indexes()
    assert (
        len(await Motor.collection.list_indexes().to_list(None)) == 5  # noqa: PLR2004
    )


async def test_ensure_all_indexes() -> None:
    await Motor.collection.drop_indexes()
    assert len(await Motor.collection.list_indexes().to_list(None)) == 1
    await Motor.ensure_all_indexes()
    assert (
        len(await Motor.collection.list_indexes().to_list(None)) == 5  # noqa: PLR2004
    )


async def test_motor_save_new() -> None:
    assert await Motor.count_documents({}) == 0

    a = Motor(value=123)
    assert not a.is_created
    a = await a.save()
    assert a.is_created

    assert await Motor.count_documents({}) == 1
    assert await Motor.collection.find_one({}) == {"_id": a.id, "value": 123}
    assert await Motor.find_one({"_id": a.id}) == a
    assert await Motor.find_one({"_id": a.id}) is not a


async def test_motor_update() -> None:
    model = MotorUnd(value=1)
    await model.save()

    value = await MotorUnd.find_one({"_id": model.id})
    assert value
    assert value.is_created
    assert isnotundefined(value.value)

    value.value += 1
    await value.save()

    value = await MotorUnd.find_one({"_id": model.id})
    assert value
    assert value.value == 2  # noqa: PLR2004

    value.value = undefined
    await value.save()

    value = await MotorUnd.find_one({"_id": model.id})
    assert value
    assert value.value is undefined


async def test_motor_delete() -> None:
    assert await Motor.count_documents({}) == 0

    models = [await Motor(value=i).save() for i in range(10)]
    assert await Motor.count_documents({}) == len(models)

    model = models[randint(0, len(models) - 1)]
    await model.delete()

    assert await Motor.count_documents({}) == len(models) - 1
    assert await Motor.count_documents({"_id": model.id}) == 0

    models.remove(model)
    for model in models:
        assert await Motor.find_one({"_id": model.id}) == model


async def test_motor_delete_error() -> None:
    with pytest.raises(ModelNotCreatedError):
        await Motor(value=1).delete()


async def test_motor_find() -> None:
    for ind in range(10):
        await Motor(value=ind).save()

    count = 0
    async for model in Motor.find({}):
        assert isinstance(model, Motor)
        count += 1

    assert count == 10  # noqa: PLR2004


async def test_motor_insert_many() -> None:
    docs = [Motor(value=ind) for ind in range(10)]
    result = await Motor.insert_many(docs, ordered=False)
    assert len(result.inserted_ids) == 10  # noqa: PLR2004


async def test_motor_update_many() -> None:
    docs = [Motor(value=ind) for ind in range(10)]
    await Motor.insert_many(docs, ordered=True)
    await Motor.update_many({}, {"$inc": {"value": 10}})
    docs = await Motor.find({}).to_list(None)
    for ind, doc in enumerate(docs):
        assert doc.value == ind + 10


async def test_motor_delete_many() -> None:
    docs = [Motor(value=ind) for ind in range(10)]
    await Motor.insert_many(docs)
    resp = await Motor.delete_many({})
    assert resp.deleted_count == 10  # noqa: PLR2004


async def test_motor_count_documents() -> None:
    docs = [Motor(value=ind) for ind in range(10)]
    await Motor.insert_many(docs)
    assert await Motor.count_documents({}) == len(docs)


async def test_motor_bulk_write() -> None:
    docs = [InsertOne({"value": 1})]
    resp = await Motor.bulk_write(docs)
    assert resp.inserted_count == 1


async def test_motor_aggregate() -> None:
    docs = [Motor(value=ind) for ind in range(10)]
    await Motor.insert_many(docs)
    pipeline = [{"$match": {"value": 3}}]
    data = await Motor.aggregate(pipeline).to_list(None)
    assert len(data) == 1


async def test_upload_file() -> None:
    data = "ololo trololo"
    id = await Motor.upload_file("file", data)  # noqa: A001
    file = await Motor.gridfs.open_download_stream(id)
    assert await file.read() == data.encode()


async def test_trigger() -> None:
    class M(Motor):
        @triggers.before_save()
        async def before_save(self) -> None:
            self.value += 1

    model = M(value=1)
    await model.save()
    assert model.value == 2  # noqa: PLR2004


@pytest.mark.parametrize("value", [None, undefined])
async def test_upload_file_empty(value: Any) -> None:
    data = await Motor.upload_file("file", value)
    assert data == value
