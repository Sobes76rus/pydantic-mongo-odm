from typing import TYPE_CHECKING
from typing import Union

from bson import ObjectId as BSONObjectId

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
            except Exception:
                raise ValueError('invalid objectid')

        if not isinstance(v, BSONObjectId):
            raise TypeError('invalid objectid')

        if not isinstance(v, ObjectId):
            v = ObjectId(v)

        return v
