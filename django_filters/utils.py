import warnings

import django
from django.conf import settings
from django.core.exceptions import FieldError
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import Expression
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ForeignObjectRel, RelatedField
from django.forms import ValidationError
from django.utils import six, timezone
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from .compat import make_aware, remote_field, remote_model
from .exceptions import FieldLookupError


def deprecate(msg, level_modifier=0):
    warnings.warn(
        "%s See: https://django-filter.readthedocs.io/en/develop/migration.html" % msg,
        DeprecationWarning, stacklevel=3 + level_modifier)


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


def get_all_model_fields(model):
    opts = model._meta

    return [
        f.name for f in sorted(opts.fields + opts.many_to_many)
        if not isinstance(f, models.AutoField) and
        not (getattr(remote_field(f), 'parent_link', False))
    ]


def get_model_field(model, field_name):
    """
    Get a ``model`` field, traversing relationships
    in the ``field_name``.

    ex::

        f = get_model_field(Book, 'author__first_name')

    """
    fields = get_field_parts(model, field_name)
    return fields[-1] if fields else None


def get_field_parts(model, field_name):
    """
    Get the field parts that represent the traversable relationships from the
    base ``model`` to the final field, described by ``field_name``.

    ex::

        >>> parts = get_field_parts(Book, 'author__first_name')
        >>> [p.verbose_name for p in parts]
        ['author', 'first name']

    """
    parts = field_name.split(LOOKUP_SEP)
    opts = model._meta
    fields = []

    # walk relationships
    for name in parts:
        try:
            field = opts.get_field(name)
        except FieldDoesNotExist:
            return None

        fields.append(field)
        if isinstance(field, RelatedField):
            opts = remote_model(field)._meta
        elif isinstance(field, ForeignObjectRel):
            opts = field.related_model._meta

    return fields


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

    try:
        while lookups:
            name = lookups[0]
            args = (lhs, name)
            if django.VERSION < (2, 0):
                # rest_of_lookups was removed in Django 2.0
                args += (lookups,)
            # If there is just one part left, try first get_lookup() so
            # that if the lhs supports both transform and lookup for the
            # name, then lookup will be picked.
            if len(lookups) == 1:
                final_lookup = lhs.get_lookup(name)
                if not final_lookup:
                    # We didn't find a lookup. We are going to interpret
                    # the name as transform, and do an Exact lookup against
                    # it.
                    lhs = query.try_transform(*args)
                    final_lookup = lhs.get_lookup('exact')
                return lhs.output_field, final_lookup.lookup_name
            lhs = query.try_transform(*args)
            lookups = lookups[1:]
    except FieldError as e:
        six.raise_from(FieldLookupError(model_field, lookup_expr), e)


def handle_timezone(value, is_dst=None):
    if settings.USE_TZ and timezone.is_naive(value):
        return make_aware(value, timezone.get_current_timezone(), is_dst)
    elif not settings.USE_TZ and timezone.is_aware(value):
        return timezone.make_naive(value, timezone.utc)
    return value


def verbose_field_name(model, field_name):
    """
    Get the verbose name for a given ``field_name``. The ``field_name``
    will be traversed across relationships. Returns '[invalid name]' for
    any field name that cannot be traversed.

    ex::

        >>> verbose_field_name(Article, 'author__name')
        'author name'

    """
    if field_name is None:
        return '[invalid name]'

    parts = get_field_parts(model, field_name)
    if not parts:
        return '[invalid name]'

    names = []
    for part in parts:
        if isinstance(part, ForeignObjectRel):
            if part.related_name:
                names.append(part.related_name.replace('_', ' '))
            else:
                return '[invalid name]'
        else:
            names.append(force_text(part.verbose_name))

    return ' '.join(names)


def verbose_lookup_expr(lookup_expr):
    """
    Get a verbose, more humanized expression for a given ``lookup_expr``.
    Each part in the expression is looked up in the ``FILTERS_VERBOSE_LOOKUPS``
    dictionary. Missing keys will simply default to itself.

    ex::

        >>> verbose_lookup_expr('year__lt')
        'year is less than'

        # with `FILTERS_VERBOSE_LOOKUPS = {}`
        >>> verbose_lookup_expr('year__lt')
        'year lt'

    """
    from .conf import settings as app_settings

    VERBOSE_LOOKUPS = app_settings.VERBOSE_LOOKUPS or {}
    lookups = [
        force_text(VERBOSE_LOOKUPS.get(lookup, _(lookup)))
        for lookup in lookup_expr.split(LOOKUP_SEP)
    ]

    return ' '.join(lookups)


def label_for_filter(model, field_name, lookup_expr, exclude=False):
    """
    Create a generic label suitable for a filter.

    ex::

        >>> label_for_filter(Article, 'author__name', 'in')
        'auther name is in'

    """
    name = verbose_field_name(model, field_name)
    verbose_expression = [_('exclude'), name] if exclude else [name]

    # iterable lookups indicate a LookupTypeField, which should not be verbose
    if isinstance(lookup_expr, six.string_types):
        verbose_expression += [verbose_lookup_expr(lookup_expr)]

    verbose_expression = [force_text(part) for part in verbose_expression if part]
    verbose_expression = capfirst(' '.join(verbose_expression))

    return verbose_expression


def raw_validation(error):
    """
    Deconstruct a django.forms.ValidationError into a primitive structure
    eg, plain dicts and lists.
    """
    if isinstance(error, ValidationError):
        if hasattr(error, 'error_dict'):
            error = error.error_dict
        elif not hasattr(error, 'message'):
            error = error.error_list
        else:
            error = error.message

    if isinstance(error, dict):
        return {key: raw_validation(value) for key, value in error.items()}
    elif isinstance(error, list):
        return [raw_validation(value) for value in error]
    else:
        return error
