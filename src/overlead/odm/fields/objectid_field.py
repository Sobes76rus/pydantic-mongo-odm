from typing import TYPE_CHECKING
from typing import Union

from bson import ObjectId as BSONObjectId
from bson.errors import InvalidId
from pydantic.json import ENCODERS_BY_TYPE

if TYPE_CHECKING:
    from pydantic.typing import CallableGenerator

ObjectIdType = Union[BSONObjectId, str]


class ObjectId(BSONObjectId):
    @classmethod
    def __get_validators__(cls) -> 'CallableGenerator':
        yield cls.validate

    @classmethod
    def validate(cls, v: ObjectIdType) -> 'ObjectId':
        if isinstance(v, str):
            try:
                v = cls(v)
            except InvalidId:
                raise ValueError('invalid objectid')

        if not isinstance(v, BSONObjectId):
            raise TypeError('invalid objectid')

        if not isinstance(v, ObjectId):
            v = ObjectId(v)

        return v

    @classmethod
    def __modify_schema__(self, field_schema):
        field_schema.update(
            type="string",
            examples=["5eb7cf5a86d9755df3a6c593", "5eb7cfb05e32e07750a1756a"],
        )


ENCODERS_BY_TYPE[BSONObjectId] = str
ENCODERS_BY_TYPE[ObjectId] = str
