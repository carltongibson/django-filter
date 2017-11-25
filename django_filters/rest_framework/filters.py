
from ..filters import BooleanFilter as _BooleanFilter
from ..filters import *
from ..widgets import BooleanWidget


class BooleanFilter(_BooleanFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', BooleanWidget)

        super().__init__(*args, **kwargs)
