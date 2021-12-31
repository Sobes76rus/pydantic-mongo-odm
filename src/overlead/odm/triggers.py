from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import ValidationError
from pydantic.error_wrappers import ErrorWrapper


class trigger():
    def __init__(self, reference_field: Optional[str] = None):
        self.reference = reference_field

    def __call__(self, func):
        self.func = func
        return self

    def exec(self, *args, **kwargs):
        yield self.func(*args, **kwargs)


class before_save(trigger):
    pass


class after_save(trigger):
    pass


class before_create(trigger):
    pass


class after_create(trigger):
    pass


class before_update(trigger):
    pass


class after_update(trigger):
    pass


class before_delete(trigger):
    pass


class after_delete(trigger):
    pass


class validator(before_save):
    def __init__(self, *fields: str):
        super().__init__()
        self.fields = fields

    def exec(self, inst: BaseModel):
        for field in self.fields:
            try:
                value: Any = yield self.func(inst, getattr(inst, field))
                setattr(inst, field, value)
            except (ValueError, TypeError, AssertionError) as exc:
                raise ValidationError([ErrorWrapper(exc, field)], inst.__class__)
