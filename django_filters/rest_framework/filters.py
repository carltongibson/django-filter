
from ..filters import *
from ..widgets import BooleanWidget


class BooleanFilter(BooleanFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', BooleanWidget)

        super(BooleanFilter, self).__init__(*args, **kwargs)
