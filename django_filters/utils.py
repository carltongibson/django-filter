
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ForeignObjectRel

from .compat import remote_model


def try_dbfield(fn, field_class):
    """
    Try ``fn`` with the DB ``field_class`` by walking its
    MRO until a result is found.

    ex::
        _try_dbfield(field_dict.get, models.CharField)

    """
    # walk the mro, as field_class could be a derived model field.
    for cls in field_class.mro():
        # skip if cls is models.Field
        if cls is models.Field:
            continue

        data = fn(cls)
        if data:
            return data


def get_model_field(model, field_name):
    """
    Get a ``model`` field, traversing relationships
    in the ``field_name``.

    ex::

        f = get_model_field(Book, 'author__first_name')

    """
    parts = field_name.split(LOOKUP_SEP)
    opts = model._meta

    # walk relationships
    for name in parts[:-1]:
        try:
            rel = opts.get_field(name)
        except FieldDoesNotExist:
            return None
        if isinstance(rel, ForeignObjectRel):
            opts = rel.related_model._meta
        else:
            opts = remote_model(rel)._meta

    try:
        return opts.get_field(parts[-1])
    except FieldDoesNotExist:
        return None
