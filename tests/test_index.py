import pytest
from pydantic import ValidationError

from overlead.odm.index import Index


@pytest.mark.parametrize('index, expect', [
    ('_id', ({'_id': 1}, {})),
    ('+key', ({'key': 1}, {})),
    ('-key', ({'key': -1}, {})),
    ('@key', ({'key': 'text'}, {})),
    ('#key', ({'key': 'hashed'}, {})),
    ('-a +b #c @d', ({'a': -1, 'b': 1, 'c': 'hashed', 'd': 'text'}, {})),
    (['a', 'b', 'c'], ({'a': 1, 'b': 1, 'c': 1}, {})),
    ({'a': 1, 'b': 1, 'c': 1}, ({'a': 1 ,'b': 1, 'c': 1}, {})),
    ([('a', -1), ('b', 1), ('c', 'hashed')], ({'a': -1, 'b': 1, 'c': 'hashed'}, {})),
    ([('a', 1)], ({'a': 1}, {})),
    (({}, {'unique': True}), ({}, {'unique': True}))
])  # yapf: disable
def test_index(index, expect):
    index = Index.parse_obj(index)
    index = index.dict()

    assert index['keys'] == expect[0]
    assert index['opts'] == expect[1]


@pytest.mark.parametrize('index', [
    {'key': 2},
    {'key': -2},
    {'key': 'asf'},
    {'key': 'hashedd'},
    '!key',
    str,
    None,
    int,
    '',
    {'': 1},
    ({}, {'unique': '123'})
])  # yapf: disable
def test_index_error(index):
    with pytest.raises(ValidationError) as exc:
        index = Index.parse_obj(index)
