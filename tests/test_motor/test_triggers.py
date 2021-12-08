import pytest

from overlead.odm import triggers
from overlead.odm.motor.model import ObjectIdModel

pytestmark = pytest.mark.asyncio


class Motor(ObjectIdModel):
    before_save: bool = False
    after_save: bool = False
    before_update: bool = False
    after_update: bool = False
    before_create: bool = False
    after_create: bool = False
    before_delete: bool = False
    after_delete: bool = False
    created: bool = False
    sync: bool = False

    class Meta:
        database_name = 'overlead-odm-test'
        collection_name = 'motor'

    @triggers.before_save()
    async def before_save_trigger(self):
        if not self.before_save:
            assert await Motor.count_documents({'before_save': True}) == 0
        self.before_save = True

    @triggers.after_save()
    async def after_save_trigger(self, created: bool):
        if not self.after_save:
            assert await Motor.count_documents({'after_save': True}) == 0
        self.after_save = True
        self.created = created

    @triggers.before_update()
    async def before_update_trigger(self):
        self.before_update = True
        assert await Motor.count_documents({'before_update': True}) == 0

    @triggers.after_update()
    async def after_update_trigger(self):
        self.after_update = True
        assert await Motor.count_documents({'after_update': True}) == 0

    @triggers.before_create()
    async def before_create_trigger(self):
        self.before_create = True
        assert await Motor.count_documents({}) == 0

    @triggers.after_create()
    async def after_create_trigger(self):
        self.after_create = True
        assert await Motor.count_documents({'_id': self.id}) == 1

    @triggers.before_save()
    def sync_trigger(self):
        self.sync = True

    @triggers.before_delete()
    async def before_delete_trigger(self):
        self.before_delete = True
        assert await Motor.count_documents({'_id': self.id}) == 1

    @triggers.after_delete()
    async def after_delete_trigger(self):
        self.after_delete = True
        assert await Motor.count_documents({'_id': self.id}) == 0


@pytest.fixture(autouse=True, scope='module')
def set_client(motor_client):
    Motor.__meta__.client = motor_client


@pytest.fixture(autouse=True, scope='function')
async def clear_database():
    await Motor.delete_many({})


async def test_before_save():
    doc = Motor()
    await doc.save()

    assert doc.before_save is True
    assert await Motor.count_documents({'before_save': True}) == 1


async def test_after_save():
    doc = Motor()
    await doc.save()

    assert doc.created is True
    assert doc.after_save is True
    assert await Motor.count_documents({'after_save': True}) == 0


async def test_before_update():
    doc = Motor()

    await doc.save()
    assert doc.before_update is False
    assert await Motor.count_documents({'before_update': True}) == 0

    await doc.save()
    assert doc.before_update is True
    assert await Motor.count_documents({'before_update': True}) == 1


async def test_after_update():
    doc = Motor()

    await doc.save()
    assert doc.created is True
    assert doc.after_update is False
    assert await Motor.count_documents({'after_update': True}) == 0

    await doc.save()
    assert doc.created is False
    assert doc.after_update is True
    assert await Motor.count_documents({'after_update': True}) == 0


async def test_before_create():
    doc = Motor()

    await doc.save()
    assert doc.before_create is True
    assert await Motor.count_documents({'before_create': True}) == 1

    doc.before_create = False
    await doc.save()
    assert doc.before_create is False
    assert await Motor.count_documents({'before_create': True}) == 0


async def test_after_create():
    doc = Motor()

    await doc.save()
    assert doc.after_create is True
    assert await Motor.count_documents({'after_create': True}) == 0

    doc.after_create = False
    await doc.save()
    assert doc.after_create is False
    assert await Motor.count_documents({'after_create': True}) == 0


async def test_sync():
    doc = Motor()

    await doc.save()
    assert doc.sync is True


async def test_before_delete():
    doc = Motor()

    await doc.save()
    assert doc.before_delete is False

    await doc.delete()
    assert doc.before_delete is True


async def test_after_delete():
    doc = Motor()

    await doc.save()
    assert doc.after_delete is False

    await doc.delete()
    assert doc.after_delete is True
