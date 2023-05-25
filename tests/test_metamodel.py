from typing import Any

import pytest
from bson import Binary
from bson.codec_options import TypeDecoder
from pydantic.main import BaseModel
from pymongo import MongoClient

from overlead.odm import triggers
from overlead.odm.metamodel import BaseMeta, BaseModelMetaclass, ModelTypeError


class CustomCodec(TypeDecoder):
    bson_type = Binary  # pyright: ignore

    def transform_bson(self, value: Any) -> Any:
        return value


class Model(BaseModel, metaclass=BaseModelMetaclass):
    ...


def test_only_pydantic_models() -> None:
    with pytest.raises(ModelTypeError):

        class Model(metaclass=BaseModelMetaclass):  #  pyright: ignore
            ...


class TestModelMeta:
    @pytest.fixture(autouse=True)
    def _meta_fixture(self) -> None:
        self.client: Any = MongoClient()

        class ModelA(BaseModel, metaclass=BaseModelMetaclass):
            @triggers.before_save()
            def method(self) -> None:
                ...

            class Meta:
                client = self.client
                collection_name = "collection_name"
                database_name = "database_name"
                indexes = ("a",)

        class ModelB(BaseModel, metaclass=BaseModelMetaclass):
            ...

        class ModelC(ModelA):
            @triggers.before_save()
            def method(self) -> None:
                ...

            class Meta:
                indexes = ("b",)
                type_codecs = (CustomCodec(),)

        self.meta1 = ModelA.__meta__
        self.meta2 = ModelB.__meta__
        self.meta3 = ModelC.__meta__

        self.modelA = ModelA
        self.modelB = ModelB
        self.modelC = ModelC

    def test_model_meta(self) -> None:
        assert issubclass(Model.__meta__, BaseMeta)

    def test_multiple_bases(self) -> None:
        assert not issubclass(self.meta1, self.meta2)
        assert not issubclass(self.meta2, self.meta1)

    def test_interitence(self) -> None:
        assert issubclass(self.meta3, self.meta1)
        assert not issubclass(self.meta1, self.meta3)

    def test_inheritence_indexes(self) -> None:
        assert self.meta1.indexes is not self.meta3.indexes
        assert self.meta1.indexes == self.meta3.indexes[: len(self.meta1.indexes)]

    def test_inheritence_triggers(self) -> None:
        assert self.meta1.triggers is not self.meta3.triggers
        assert self.meta1.triggers == self.meta3.triggers[: len(self.meta1.triggers)]

    def test_inheritence_type_codecs(self) -> None:
        assert self.meta1.type_codecs is not self.meta3.type_codecs
        assert (
            self.meta1.type_codecs
            == self.meta3.type_codecs[: len(self.meta1.type_codecs)]
        )

    def test_inheritence_client(self) -> None:
        assert self.meta1.client is self.meta3.client
        assert self.meta1.client is self.client

    def test_inheritence_database_name(self) -> None:
        assert self.meta1.database_name is self.meta3.database_name
        assert self.meta1.database_name == "database_name"

    def test_inheritence_collection_name(self) -> None:
        assert self.meta1.collection_name is self.meta3.collection_name
        assert self.meta1.collection_name == "collection_name"

    def test_config_client(self) -> None:
        assert self.modelC.__config__.overlead_meta == self.meta3  # type: ignore[attr-defined] # noqa: E501
        assert self.modelA.__config__.overlead_meta == self.meta1  # type: ignore[attr-defined] # noqa: E501

    def test_config_client_with_config(self) -> None:
        class ModelTest(self.modelA):  # type: ignore[name-defined, misc]
            class Config:
                ololo = 123

        assert (
            ModelTest.__config__.overlead_meta == ModelTest.__meta__  # pyright: ignore
        )


class TestModelTriggers:
    def test_removal(self) -> None:
        class Model(BaseModel, metaclass=BaseModelMetaclass):
            @triggers.after_create()
            def method(self) -> None:
                ...

        with pytest.raises(AttributeError):
            Model.method

    def test_inheritence(self) -> None:
        class ModelA(BaseModel, metaclass=BaseModelMetaclass):
            @triggers.after_create()
            def method(self) -> None:
                ...

        class ModelB(ModelA, metaclass=BaseModelMetaclass):
            @triggers.after_create()
            def method(self) -> None:
                ...

        assert len(ModelA.__meta__.triggers) == 1
        assert len(ModelB.__meta__.triggers) == 2  # noqa: PLR2004

    def test_registry(self) -> None:
        class ModelA(BaseModel, metaclass=BaseModelMetaclass):
            ...

        class ModelB(BaseModel, metaclass=BaseModelMetaclass):
            ...

        class ModelAA(ModelA):
            ...

        assert ModelA.__registry__ is ModelAA.__registry__
        assert ModelA.__registry__ is not ModelB.__registry__
        assert ModelA.__registry__ == [ModelA, ModelAA]
        assert ModelB.__registry__ == [ModelB]
