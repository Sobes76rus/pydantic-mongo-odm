from typing import Optional


class trigger():
    def __init__(self, reference_field: Optional[str] = None):
        self.reference = reference_field

    def __call__(self, func):
        self.func = func
        return self


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
