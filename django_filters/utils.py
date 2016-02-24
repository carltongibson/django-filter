from django.conf import settings
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import Expression
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ForeignObjectRel
from django.utils import timezone

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


def resolve_field(model_field, lookup_expr):
    """
    Resolves a ``lookup_expr`` into its final output field, given
    the initial ``model_field``. The lookup expression should only contain
    transforms and lookups, not intermediary model field parts.

    Note:
    This method is based on django.db.models.sql.query.Query.build_lookup

    For more info on the lookup API:
    https://docs.djangoproject.com/en/1.9/ref/models/lookups/

    """
    query = model_field.model._default_manager.all().query
    lhs = Expression(model_field)
    lookups = lookup_expr.split(LOOKUP_SEP)

    assert len(lookups) > 0

    while lookups:
        name = lookups[0]
        # If there is just one part left, try first get_lookup() so
        # that if the lhs supports both transform and lookup for the
        # name, then lookup will be picked.
        if len(lookups) == 1:
            final_lookup = lhs.get_lookup(name)
            if not final_lookup:
                # We didn't find a lookup. We are going to interpret
                # the name as transform, and do an Exact lookup against
                # it.
                lhs = query.try_transform(lhs, name, lookups)
                final_lookup = lhs.get_lookup('exact')
            return lhs.output_field, final_lookup.lookup_name
        lhs = query.try_transform(lhs, name, lookups)
        lookups = lookups[1:]


def handle_timezone(value):
    if settings.USE_TZ and timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_default_timezone())
    elif not settings.USE_TZ and timezone.is_aware(value):
        return timezone.make_naive(value, timezone.UTC())
    return value
