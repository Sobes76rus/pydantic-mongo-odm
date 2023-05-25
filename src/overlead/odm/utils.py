import pickle
from collections.abc import Callable
from typing import Any, TypeVar

import orjson
from bson import Binary
from bson.binary import USER_DEFINED_SUBTYPE
from bson.codec_options import TypeDecoder
from pydantic.typing import is_namedtuple as _is_namedtuple
from pydantic.utils import sequence_like as _sequence_like

from overlead.odm.types import undefined

T = TypeVar("T", bound=object)


def exclude_values(v: T, value: tuple[Any, ...]) -> T:
    """Исключить указанные значение из обьекта."""
    if isinstance(v, dict):
        return {  # type: ignore[return-value]
            k: exclude_values(v, value) for k, v in v.items() if v not in value
        }

    if _sequence_like(v):
        seq = (
            exclude_values(val, value)
            for val in v  # type: ignore[attr-defined]
            if val not in value
        )
        return (
            v.__class__(*seq)  # pyright: ignore
            if _is_namedtuple(v.__class__)
            else v.__class__(seq)  # type: ignore[call-arg]
        )

    return v


def exclude_undefined_values(v: T) -> T:
    """Исключить undefined."""
    return exclude_values(v, (undefined,))


def exclude_none_values(v: T) -> T:
    """Искключить None."""
    return exclude_values(v, (None,))


def exclude_nullable_values(v: T) -> T:
    """Исключить None и undefined."""
    return exclude_values(v, (undefined, None))


def json_dumps(
    v: Any,
    *,
    default: Callable[..., Any],
    exclude_undefined: bool = True,
) -> str:
    """Сереализация для JSON."""
    if exclude_undefined:
        v = exclude_undefined_values(v)

    return orjson.dumps(v, default=default).decode()


def fallback_pickle_encoder(value: Any) -> Binary:
    """Сереализация данных для MongoDB для кастомных обьектов."""
    return Binary(pickle.dumps(value), USER_DEFINED_SUBTYPE)


class PickledBinaryDecoder(TypeDecoder):
    """Десереализатор для MongoDB."""

    bson_type = Binary  # pyright: ignore

    def transform_bson(self, value: Any) -> Any:
        """Десереализация кастомных обьектов."""
        if value.subtype == USER_DEFINED_SUBTYPE:
            return pickle.loads(value)

        return value
