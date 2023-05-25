from __future__ import annotations

from typing import TYPE_CHECKING

from bson import ObjectId as BSONObjectId
from pydantic.json import ENCODERS_BY_TYPE
from pydantic.utils import lenient_issubclass

from overlead.odm.fields import ObjectId, Reference
from overlead.odm.types import UndefinedType

if TYPE_CHECKING:
    from pydantic.fields import ModelField

ENCODERS_BY_TYPE[BSONObjectId] = str
ENCODERS_BY_TYPE[ObjectId] = str
ENCODERS_BY_TYPE[Reference] = str
ENCODERS_BY_TYPE[UndefinedType] = str


SCALAR_TYPES: list[type] = [Reference, UndefinedType]
SCALAR_GENERIC_TYPES: list[type] = []

try:
    import fastapi
    import fastapi.dependencies.utils
    import fastapi.params

    def is_scalar_field_patch(field: ModelField) -> bool:
        """Check scalars."""
        if lenient_issubclass(field.type_, tuple(SCALAR_TYPES)) and not isinstance(
            field.field_info,
            fastapi.params.Body,
        ):
            return True

        if (
            lenient_issubclass(field.type_, tuple(SCALAR_GENERIC_TYPES))
            and not isinstance(field.field_info, fastapi.params.Body)
            and all(is_scalar_field_patch(f) for f in field.sub_fields or [])
        ):
            return True

        return is_scalar_field(field)

    is_scalar_field = fastapi.dependencies.utils.is_scalar_field
    fastapi.dependencies.utils.is_scalar_field = is_scalar_field_patch

except ModuleNotFoundError:
    pass
