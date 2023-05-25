from __future__ import annotations

import pickle

import orjson
import pytest
from bson import ObjectId
from gridfs.errors import FileExists, NoFile
from pydantic import ValidationError

from overlead.odm.fields.file_field import (
    FileField,  # noqa: TCH001
    JsonFileField,  # noqa: TCH001
    PickleFileField,  # noqa: TCH001
)
from overlead.odm.motor import ObjectIdModel


class Model(ObjectIdModel):
    file: FileField


class ModelJson(ObjectIdModel):
    file: JsonFileField[str]


class ModelPickle(ObjectIdModel):
    file: PickleFileField[str]


class TestFileField:
    async def test_write(self) -> None:
        model = Model(file=ObjectId())  # type: ignore[arg-type]
        await model.file.write("test", b"hello world")
        assert await model.file.read() == b"hello world"

    async def test_write_error(self) -> None:
        model = Model(
            file=await Model.upload_file(  # type: ignore[arg-type]
                "test",
                "hello world",
            ),
        )
        with pytest.raises(FileExists):
            await model.file.write("test", b"world hello")

    async def test_delete(self) -> None:
        model = Model(file=ObjectId())  # type: ignore[arg-type]
        await model.file.write("test", b"hello world")
        await model.file.delete()
        with pytest.raises(NoFile):
            await model.file.read()


async def test_json_dump() -> None:
    value = "hello world"
    model = ModelJson(file=ObjectId())  # type: ignore[arg-type]
    await model.file.dump("test", value)
    assert await model.file.read() == orjson.dumps(value)


async def test_pickle_dump() -> None:
    value = "hello world"
    model = ModelPickle(file=ObjectId())  # type: ignore[arg-type]
    await model.file.dump("test", value)
    assert await model.file.read() == pickle.dumps(value)


async def test_json_load() -> None:
    value_text = "Hello world!"
    id = await ModelJson.upload_file(  # noqa: A001
        "test-name",
        orjson.dumps(value_text),
    )
    a = ModelJson(file=id)  # type: ignore[arg-type]

    assert a.file == id
    assert await a.file.load() == value_text


async def test_json_load_error() -> None:
    value = ["1", "3"]
    id = await ModelJson.upload_file("test-name", orjson.dumps(value))  # noqa: A001
    with pytest.raises(ValidationError):
        await ModelJson(file=id).file.load()  # type: ignore[arg-type]
