from random import randint

import pytest

from overlead.odm.motor.model import ObjectIdModel


class Motor(ObjectIdModel):
    value: int

    class Meta:
        collection_name = 'motor'
        indexes = ('value', {'value': 'hashed'}, ('-value', {'unique': True}), ['_id', 'value'])


@pytest.fixture(autouse=True, scope='module')
async def create_collection():
    await Motor.database.create_collection(Motor.collection_name)


async def test_ensure_indexes():
    await Motor.collection.drop_indexes()
    assert len(await Motor.collection.list_indexes().to_list(None)) == 1
    await Motor.ensure_indexes()
    assert len(await Motor.collection.list_indexes().to_list(None)) == 5


async def test_ensure_all_indexes():
    await Motor.collection.drop_indexes()
    assert len(await Motor.collection.list_indexes().to_list(None)) == 1
    await ObjectIdModel.ensure_all_indexes()
    assert len(await Motor.collection.list_indexes().to_list(None)) == 5


async def test_motor_save_new():
    assert await Motor.count_documents({}) == 0

    a = Motor(value=123)
    a = await a.save()

    assert await Motor.count_documents({}) == 1
    assert await Motor.collection.find_one({}) == {'_id': a.id, 'value': 123}
    assert await Motor.find_one({'_id': a.id}) == a
    assert await Motor.find_one({'_id': a.id}) is not a


async def test_motor_delete():
    assert await Motor.count_documents({}) == 0

    models = [await Motor(value=i).save() for i in range(10)]
    assert await Motor.count_documents({}) == len(models)

    model = models[randint(0, len(models) - 1)]
    await model.delete()

    assert await Motor.count_documents({}) == len(models) - 1
    assert await Motor.count_documents({'_id': model.id}) == 0

    models.remove(model)
    for model in models:
        assert await Motor.find_one({'_id': model.id}) == model
