from __future__ import annotations

from bson import ObjectId as BSONObjectId
from pydantic.fields import ModelField
from pydantic.json import ENCODERS_BY_TYPE

from overlead.odm.fields import ObjectId
from overlead.odm.fields import Reference
from overlead.odm.types import UndefinedClass

ENCODERS_BY_TYPE[BSONObjectId] = str
ENCODERS_BY_TYPE[ObjectId] = str
ENCODERS_BY_TYPE[Reference] = str

SCALAR_TYPES: list[type] = [Reference]
SCALAR_GENERIC_TYPES: list[type] = [UndefinedClass]

try:
    import fastapi
    import fastapi.dependencies.utils
    import fastapi.params

    def is_scalar_field_patch(field: ModelField) -> bool:
        if lenient_issubclass(field.type_, SCALAR_TYPES)\
                and not isinstance(field.field_info, fastapi.params.Body):
            return True

        if lenient_issubclass(field.type_, SCALAR_GENERIC_TYPES)\
                and not isinstance(field.field_info, fastapi.params.Body)\
                and all(is_scalar_field_patch(f) for f in field.sub_fields):
            return True

        return is_scalar_field(field)

    is_scalar_field = fastapi.dependencies.utils.is_scalar_field
    fastapi.dependencies.utils.is_scalar_field = is_scalar_field_patch

except ModuleNotFoundError:
    pass
