
from django.core.exceptions import FieldError


class FieldLookupError(FieldError):
    def __init__(self, model_field, lookup_expr):
        super(FieldLookupError, self).__init__(
            "Unsupported lookup '%s' for field '%s'." % (lookup_expr, model_field)
        )
