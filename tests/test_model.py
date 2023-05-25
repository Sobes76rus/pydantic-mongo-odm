from typing import Any, TypeAlias

import orjson
import pytest

from overlead.odm import triggers
from overlead.odm.client import get_client
from overlead.odm.errors import (
    ModelClientError,
    ModelCollectionNameError,
    ModelDatabaseNameError,
)
from overlead.odm.index import Index
from overlead.odm.model import BaseModel
from overlead.odm.types import Undefined, undefined
from overlead.odm.utils import PickledBinaryDecoder

X: TypeAlias = BaseModel[int]


class ModelTest(X):
    value: str | None
    value_u: Undefined[str] = undefined

    class Meta:
        client = get_client()
        database_name = "database_name"
        collection_name = "collection_name"


class TestModelType:
    def test_meta_indexes(self) -> None:
        meta = BaseModel.__meta__
        assert meta.indexes == (Index.parse_obj("_id"),)

    def test_meta_type_codecs(self) -> None:
        meta = BaseModel.__meta__
        match meta.type_codecs:
            case (PickledBinaryDecoder(),):
                ...
            case _:  # pragma: no cover
                pytest.fail(f"{meta.type_codecs}")

    def test_client(self) -> None:
        assert ModelTest.client == get_client()

    def test_no_client(self) -> None:
        with pytest.raises(ModelClientError):
            BaseModel.client

    def test_invalid_client(self) -> None:
        BaseModel.__meta__.client = 123  # type: ignore[assignment]
        with pytest.raises(ModelClientError):
            BaseModel.client

    def test_database_name(self) -> None:
        assert ModelTest.database_name == "database_name"

    def test_no_database_name(self) -> None:
        with pytest.raises(ModelDatabaseNameError):
            BaseModel.database_name

    def test_invalid_database_name(self) -> None:
        BaseModel.__meta__.database_name = 123  # type: ignore[assignment]
        with pytest.raises(ModelDatabaseNameError):
            BaseModel.database_name

    def test_collection_name(self) -> None:
        assert ModelTest.collection_name == "collection_name"

    def test_no_collection_name(self) -> None:
        with pytest.raises(ModelCollectionNameError):
            BaseModel.collection_name

    def test_invalid_collection_name(self) -> None:
        BaseModel.__meta__.collection_name = 123  # type: ignore[assignment]
        with pytest.raises(ModelCollectionNameError):
            BaseModel.collection_name

    def test_database(self) -> None:
        assert ModelTest.database == ModelTest.client["database_name"]

    def test_collection(self) -> None:
        assert (
            ModelTest.collection == ModelTest.client["database_name"]["collection_name"]
        )

    def test_load(self) -> None:
        value = 123
        model = ModelTest._load({"_id": 123, "value": "test value"})  # noqa: SLF001
        assert model.id == value
        assert model.value == "test value"
        assert model._olds == {"_id": 123, "value": "test value"}  # noqa: SLF001

    def test_get_triggers(self) -> None:
        class Model(BaseModel[Any]):
            @triggers.before_save()
            def a(self) -> None:  # pragma: no cover
                ...

            @triggers.before_delete()
            def b(self) -> None:  # pragma: no cover
                ...

        assert len(list(Model._get_triggers(triggers.before_save))) == 1
        assert len(list(Model._get_triggers(triggers.trigger))) == 2  # noqa: PLR2004
        assert len(list(Model._get_triggers(triggers.after_save))) == 0
        assert len(list(Model._get_triggers(triggers.before_delete))) == 1


class TestModelInstance:
    @pytest.fixture(autouse=True)
    def _model_fixture(self) -> None:
        self.model = ModelTest(value="test value")

    def test_is_created(self) -> None:
        assert not self.model.is_created
        self.model.id = 123
        assert self.model.is_created

    def test_dict(self) -> None:
        assert self.model.dict() == {"value": "test value"}
        self.model.value = None
        assert self.model.dict() == {"value": None}

    def test_dump(self) -> None:
        assert self.model._dump() == {"value": "test value"}  # noqa: SLF001
        self.model.value = None
        assert self.model._dump() == {"value": None}  # noqa: SLF001

    def test_dump_undefined(self) -> None:
        model = ModelTest(value_u="some value", value="some value")
        assert model._dump() == {  # noqa: SLF001
            "value": "some value",
            "value_u": "some value",
        }
        model.value = None
        model.value_u = undefined
        assert model._dump() == {"value": None}  # noqa: SLF001

    def test_dump_default(self) -> None:
        class Model(BaseModel[Any]):
            a: Undefined[str] = undefined
            b: str | None = None
            c: str = "value c"

        model = Model()
        assert model._dump() == {"b": None, "c": "value c"}  # noqa: SLF001

    def test_json_undefined(self) -> None:
        class Model(BaseModel[Any]):
            a: Undefined[str] = undefined
            b: str | None = None
            c: str = "value c"

        model = Model()
        assert model.json() == orjson.dumps({"b": None, "c": "value c"}).decode()


@pytest.mark.skip()
def test_schema() -> None:
    assert ModelTest.schema()


@pytest.mark.skip()
def test_schema_json() -> None:
    assert ModelTest.schema_json() is None
