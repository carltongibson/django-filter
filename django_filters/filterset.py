from __future__ import absolute_import
from __future__ import unicode_literals

import copy
from collections import OrderedDict

from django import forms
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import ForeignObjectRel
from django.utils import six

from .conf import settings
from .compat import remote_field, remote_queryset
from .constants import ALL_FIELDS, STRICTNESS, EMPTY_VALUES
from .filters import (Filter, CharFilter, BooleanFilter, BaseInFilter, BaseRangeFilter,
                      ChoiceFilter, DateFilter, DateTimeFilter, TimeFilter, ModelChoiceFilter,
                      ModelMultipleChoiceFilter, NumberFilter, UUIDFilter, DurationFilter)
from .utils import try_dbfield, get_all_model_fields, get_model_field, resolve_field


def get_filter_name(field_name, lookup_expr):
    """
    Combine a field name and lookup expression into a usable filter name.
    Exact lookups are the implicit default, so "exact" is stripped from the
    end of the filter name.
    """
    filter_name = LOOKUP_SEP.join([field_name, lookup_expr])

    # This also works with transformed exact lookups, such as 'date__exact'
    _exact = LOOKUP_SEP + 'exact'
    if filter_name.endswith(_exact):
        filter_name = filter_name[:-len(_exact)]

    return filter_name


def _together_valid(form, fieldset):
    field_presence = [
        form.cleaned_data.get(field) not in EMPTY_VALUES
        for field in fieldset
    ]

    if any(field_presence):
        return all(field_presence)
    return True


def get_full_clean_override(together):
    # coerce together to list of pairs
    if isinstance(together[0], (six.string_types)):
        together = [together]

    def full_clean(form):
        super(form.__class__, form).full_clean()
        message = 'Following fields must be together: %s'

        for each in together:
            if not _together_valid(form, each):
                return form.add_error(None, message % ','.join(each))

    return full_clean


class FilterSetOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)

        self.filter_overrides = getattr(options, 'filter_overrides', {})

        self.strict = getattr(options, 'strict', None)

        self.form = getattr(options, 'form', forms.Form)

        self.together = getattr(options, 'together', None)


class FilterSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['declared_filters'] = cls.get_declared_filters(bases, attrs)

        new_class = super(FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)
        new_class._meta = FilterSetOptions(getattr(new_class, 'Meta', None))
        new_class.base_filters = new_class.get_filters()

        return new_class

    @classmethod
    def get_declared_filters(cls, bases, attrs):
        filters = [
            (filter_name, attrs.pop(filter_name))
            for filter_name, obj in list(attrs.items())
            if isinstance(obj, Filter)
        ]

        # Default the `filter.name` to the attribute name on the filterset
        for filter_name, f in filters:
            if getattr(f, 'name', None) is None:
                f.name = filter_name

        filters.sort(key=lambda x: x[1].creation_counter)

        # merge declared filters from base classes
        for base in reversed(bases):
            if hasattr(base, 'declared_filters'):
                filters = [
                    (name, f) for name, f
                    in base.declared_filters.items()
                    if name not in attrs
                ] + filters

        return OrderedDict(filters)


FILTER_FOR_DBFIELD_DEFAULTS = {
    models.AutoField:                   {'filter_class': NumberFilter},
    models.CharField:                   {'filter_class': CharFilter},
    models.TextField:                   {'filter_class': CharFilter},
    models.BooleanField:                {'filter_class': BooleanFilter},
    models.DateField:                   {'filter_class': DateFilter},
    models.DateTimeField:               {'filter_class': DateTimeFilter},
    models.TimeField:                   {'filter_class': TimeFilter},
    models.DurationField:               {'filter_class': DurationFilter},
    models.DecimalField:                {'filter_class': NumberFilter},
    models.SmallIntegerField:           {'filter_class': NumberFilter},
    models.IntegerField:                {'filter_class': NumberFilter},
    models.PositiveIntegerField:        {'filter_class': NumberFilter},
    models.PositiveSmallIntegerField:   {'filter_class': NumberFilter},
    models.FloatField:                  {'filter_class': NumberFilter},
    models.NullBooleanField:            {'filter_class': BooleanFilter},
    models.SlugField:                   {'filter_class': CharFilter},
    models.EmailField:                  {'filter_class': CharFilter},
    models.FilePathField:               {'filter_class': CharFilter},
    models.URLField:                    {'filter_class': CharFilter},
    models.GenericIPAddressField:       {'filter_class': CharFilter},
    models.CommaSeparatedIntegerField:  {'filter_class': CharFilter},
    models.UUIDField:                   {'filter_class': UUIDFilter},
    models.OneToOneField: {
        'filter_class': ModelChoiceFilter,
        'extra': lambda f: {
            'queryset': remote_queryset(f),
            'to_field_name': remote_field(f).field_name,
        }
    },
    models.ForeignKey: {
        'filter_class': ModelChoiceFilter,
        'extra': lambda f: {
            'queryset': remote_queryset(f),
            'to_field_name': remote_field(f).field_name,
        }
    },
    models.ManyToManyField: {
        'filter_class': ModelMultipleChoiceFilter,
        'extra': lambda f: {
            'queryset': remote_queryset(f),
        }
    },
}


class BaseFilterSet(object):
    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS

    def __init__(self, data=None, queryset=None, prefix=None, strict=None, request=None):
        self.is_bound = data is not None
        self.data = data or {}
        if queryset is None:
            queryset = self._meta.model._default_manager.all()
        self.queryset = queryset
        self.form_prefix = prefix

        # What to do on on validation errors
        # Fallback to meta, then settings strictness
        if strict is None:
            strict = self._meta.strict
        if strict is None:
            strict = settings.STRICTNESS

        # transform legacy values
        self.strict = STRICTNESS._LEGACY.get(strict, strict)

        self.request = request

        self.filters = copy.deepcopy(self.base_filters)

        for filter_ in self.filters.values():
            # propagate the model and filterset to the filters
            filter_.model = self._meta.model
            filter_.parent = self

    @property
    def qs(self):
        if not hasattr(self, '_qs'):
            if not self.is_bound:
                self._qs = self.queryset.all()
                return self._qs

            if not self.form.is_valid():
                if self.strict == STRICTNESS.RAISE_VALIDATION_ERROR:
                    raise forms.ValidationError(self.form.errors)
                elif self.strict == STRICTNESS.RETURN_NO_RESULTS:
                    self._qs = self.queryset.none()
                    return self._qs
                # else STRICTNESS.IGNORE...  ignoring

            # start with all the results and filter from there
            qs = self.queryset.all()
            for name, filter_ in six.iteritems(self.filters):
                value = self.form.cleaned_data.get(name)

                if value is not None:  # valid & clean data
                    qs = filter_.filter(qs, value)

            self._qs = qs

        return self._qs

    @property
    def form(self):
        if not hasattr(self, '_form'):
            fields = OrderedDict([
                (name, filter_.field)
                for name, filter_ in six.iteritems(self.filters)])

            Form = type(str('%sForm' % self.__class__.__name__),
                        (self._meta.form,), fields)
            if self._meta.together:
                Form.full_clean = get_full_clean_override(self._meta.together)
            if self.is_bound:
                self._form = Form(self.data, prefix=self.form_prefix)
            else:
                self._form = Form(prefix=self.form_prefix)
        return self._form

    @classmethod
    def get_fields(cls):
        """
        Resolve the 'fields' argument that should be used for generating filters on the
        filterset. This is 'Meta.fields' sans the fields in 'Meta.exclude'.
        """
        model = cls._meta.model
        fields = cls._meta.fields
        exclude = cls._meta.exclude

        assert not (fields is None and exclude is None), \
            "Setting 'Meta.model' without either 'Meta.fields' or 'Meta.exclude' " \
            "has been deprecated since 0.15.0 and is now disallowed. Add an explicit " \
            "'Meta.fields' or 'Meta.exclude' to the %s class." % cls.__name__

        # Setting exclude with no fields implies all other fields.
        if exclude is not None and fields is None:
            fields = ALL_FIELDS

        # Resolve ALL_FIELDS into all fields for the filterset's model.
        if fields == ALL_FIELDS:
            fields = get_all_model_fields(model)

        # Remove excluded fields
        exclude = exclude or []
        if not isinstance(fields, dict):
            fields = [(f, ['exact']) for f in fields if f not in exclude]
        else:
            fields = [(f, lookups) for f, lookups in fields.items() if f not in exclude]

        return OrderedDict(fields)

    @classmethod
    def get_filters(cls):
        """
        Get all filters for the filterset. This is the combination of declared and
        generated filters.
        """

        # No model specified - skip filter generation
        if not cls._meta.model:
            return cls.declared_filters.copy()

        # Determine the filters that should be included on the filterset.
        filters = OrderedDict()
        fields = cls.get_fields()
        undefined = []

        for field_name, lookups in fields.items():
            field = get_model_field(cls._meta.model, field_name)

            # warn if the field doesn't exist.
            if field is None:
                undefined.append(field_name)

            # ForeignObjectRel does not support non-exact lookups
            if isinstance(field, ForeignObjectRel):
                filters[field_name] = cls.filter_for_reverse_field(field, field_name)
                continue

            for lookup_expr in lookups:
                filter_name = get_filter_name(field_name, lookup_expr)

                # If the filter is explicitly declared on the class, skip generation
                if filter_name in cls.declared_filters:
                    filters[filter_name] = cls.declared_filters[filter_name]
                    continue

                if field is not None:
                    filters[filter_name] = cls.filter_for_field(field, field_name, lookup_expr)

        # filter out declared filters
        undefined = [f for f in undefined if f not in cls.declared_filters]
        if undefined:
            raise TypeError(
                "'Meta.fields' contains fields that are not defined on this FilterSet: "
                "%s" % ', '.join(undefined)
            )

        # Add in declared filters. This is necessary since we don't enforce adding
        # declared filters to the 'Meta.fields' option
        filters.update(cls.declared_filters)
        return filters

    @classmethod
    def filter_for_field(cls, f, name, lookup_expr='exact'):
        f, lookup_type = resolve_field(f, lookup_expr)

        default = {
            'name': name,
            'lookup_expr': lookup_expr,
        }

        filter_class, params = cls.filter_for_lookup(f, lookup_type)
        default.update(params)

        assert filter_class is not None, (
            "%s resolved field '%s' with '%s' lookup to an unrecognized field "
            "type %s. Try adding an override to 'Meta.filter_overrides'. See: "
            "https://django-filter.readthedocs.io/en/develop/ref/filterset.html#customise-filter-generation-with-filter-overrides"
        ) % (cls.__name__, name, lookup_expr, f.__class__.__name__)

        return filter_class(**default)

    @classmethod
    def filter_for_reverse_field(cls, f, name):
        rel = remote_field(f.field)
        queryset = f.field.model._default_manager.all()
        default = {
            'name': name,
            'queryset': queryset,
        }
        if rel.multiple:
            return ModelMultipleChoiceFilter(**default)
        else:
            return ModelChoiceFilter(**default)

    @classmethod
    def filter_for_lookup(cls, f, lookup_type):
        DEFAULTS = dict(cls.FILTER_DEFAULTS)
        if hasattr(cls, '_meta'):
            DEFAULTS.update(cls._meta.filter_overrides)

        data = try_dbfield(DEFAULTS.get, f.__class__) or {}
        filter_class = data.get('filter_class')
        params = data.get('extra', lambda f: {})(f)

        # if there is no filter class, exit early
        if not filter_class:
            return None, {}

        # perform lookup specific checks
        if lookup_type == 'exact' and f.choices:
            return ChoiceFilter, {'choices': f.choices}

        if lookup_type == 'isnull':
            data = try_dbfield(DEFAULTS.get, models.BooleanField)

            filter_class = data.get('filter_class')
            params = data.get('extra', lambda f: {})(f)
            return filter_class, params

        if lookup_type == 'in':
            class ConcreteInFilter(BaseInFilter, filter_class):
                pass
            ConcreteInFilter.__name__ = cls._csv_filter_class_name(
                filter_class, lookup_type
            )

            return ConcreteInFilter, params

        if lookup_type == 'range':
            class ConcreteRangeFilter(BaseRangeFilter, filter_class):
                pass
            ConcreteRangeFilter.__name__ = cls._csv_filter_class_name(
                filter_class, lookup_type
            )

            return ConcreteRangeFilter, params

        return filter_class, params

    @classmethod
    def _csv_filter_class_name(cls, filter_class, lookup_type):
        """
        Generate a suitable class name for a concrete filter class. This is not
        completely reliable, as not all filter class names are of the format
        <Type>Filter.

        ex::

            FilterSet._csv_filter_class_name(DateTimeFilter, 'in')

            returns 'DateTimeInFilter'

        """
        # DateTimeFilter => DateTime
        type_name = filter_class.__name__
        if type_name.endswith('Filter'):
            type_name = type_name[:-6]

        # in => In
        lookup_name = lookup_type.capitalize()

        # DateTimeInFilter
        return str('%s%sFilter' % (type_name, lookup_name))


class FilterSet(six.with_metaclass(FilterSetMetaclass, BaseFilterSet)):
    pass


def filterset_factory(model, fields=ALL_FIELDS):
    meta = type(str('Meta'), (object,), {'model': model, 'fields': fields})
    filterset = type(str('%sFilterSet' % model._meta.object_name),
                     (FilterSet,), {'Meta': meta})
    return filterset
