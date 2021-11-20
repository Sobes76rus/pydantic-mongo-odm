from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from typing import Awaitable
from typing import Generic
from typing import Type
from typing import TypeVar
from typing import Union
from typing import overload

from pydantic.fields import ModelField
from pydantic.json import ENCODERS_BY_TYPE

from overlead.odm.fields.objectid_field import ObjectId
from overlead.odm.fields.objectid_field import ObjectIdType
from overlead.odm.model import BaseModel

M = TypeVar('M', bound=BaseModel)

if TYPE_CHECKING:
    from overlead.odm.motor.model import MotorModel
    MM = TypeVar('MM', bound=MotorModel)


class DeleteRule(str, enum.Enum):
    NOTHING = 'NOTHING'
    NULLIFY = 'NULLIFY'
    CASCADE = 'CASCADE'
    DENY = 'DENY'


class Reference(ObjectId, Generic[M]):
    type_: Type[M]
    field: ModelField

    def __init__(self, v: ObjectIdType, type_: Type[M], field: ModelField) -> None:
        super().__init__(v)

        if not issubclass(type_, BaseModel):
            raise TypeError(f'invalid reference: {type_}')

        self.type_ = type_
        self.field = field

    @classmethod
    def validate(cls, v: Union[ObjectIdType, BaseModel], field: ModelField) -> Reference[M]:
        if not field.sub_fields:
            raise TypeError('required')

        type_ = field.sub_fields[0].type_

        if not issubclass(type_, BaseModel):
            raise TypeError(f'invalid reference: {type_}')

        if isinstance(v, Reference):
            if v.type_ != type_:
                raise TypeError(f'invalid reference: {v.type_}')

            return v

        if isinstance(v, type_):
            if v.is_created:
                return cls(v.id, type_, field)

            raise ValueError('document is not created')

        return cls(ObjectId.validate(v), type_, field)

    @overload
    def load(self: Reference['MM']) -> Awaitable['MM']:
        ...

    @overload
    def load(self: Reference[M]) -> M:
        ...

    def load(self):
        return self.type_.find_one({'_id': self})

    @classmethod
    def __modify_schema__(self, field_schema):
        field_schema.update(
            type='string',
            examples=["5eb7cf5a86d9755df3a6c593", "5eb7cfb05e32e07750a1756a"],
        )

    def __getstate__(self):
        state = self.__dict__.copy()
        state['_ObjectId__id'] = self._ObjectId__id
        del state['field']
        return state

    def __setstate__(self, state):
        self._ObjectId__id = state.pop('_ObjectId__id')
        self.__dict__.update(state)


ENCODERS_BY_TYPE[Reference] = str
