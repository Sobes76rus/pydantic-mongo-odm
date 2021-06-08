import pytest
from pydantic import ValidationError

from overlead.odm.model import BaseModel


class ModelA(BaseModel):
    class Meta:
        indexes = [
            'a',
            '+b',
            '-a',
            ('a', {'unique': True}),
        ]  # yapf: disable


def test_indexes_good():
    indexes = ModelA.__meta__.indexes
    indexes = [i.dict() for i in indexes]
    assert indexes == [
        {'keys': {'_id': 1}, 'opts': {}},
        {'keys': {'a': 1}, 'opts': {}},
        {'keys': {'b': 1}, 'opts': {}},
        {'keys': {'a': -1}, 'opts': {}},
        {'keys': {'a': 1}, 'opts': {'unique': True}},
    ]   # yapf: disable


def test_indexes_bad():
    with pytest.raises(TypeError) as exc:

        class ModelBad(BaseModel):
            class Meta:
                indexes = 'a'
