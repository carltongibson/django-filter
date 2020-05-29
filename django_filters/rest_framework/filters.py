from django_filters import filters

from ..filters import *  # noqa
from ..widgets import BooleanWidget

__all__ = filters.__all__


class BooleanFilter(filters.BooleanFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', BooleanWidget)

        super().__init__(*args, **kwargs)


class IsoDateTimeFromToRangeFilter(filters.IsoDateTimeFromToRangeFilter):
    def get_schema_operation_parameters(self, field_name):
        return [
            {
                "name": field_name + "_before",
                "required": self.extra["required"],
                "in": "query",
                "description": self.label + " formatted according to ISO 8601"
                if self.label is not None
                else field_name,
                "schema": {"type": "string", "format": "dateTime"},
            },
            {
                "name": field_name + "_after",
                "required": self.extra["required"],
                "in": "query",
                "description": self.label + " formatted according to ISO 8601"
                if self.label is not None
                else field_name,
                "schema": {"type": "string", "format": "dateTime"},
            },
        ]
