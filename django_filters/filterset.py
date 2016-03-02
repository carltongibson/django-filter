from __future__ import absolute_import
from __future__ import unicode_literals

import copy
import re
from collections import OrderedDict

from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.core.validators import EMPTY_VALUES
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import ForeignObjectRel
from django.utils import six
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from .compat import remote_field, remote_model
from .filters import (Filter, CharFilter, BooleanFilter, BaseInFilter, BaseRangeFilter,
                      ChoiceFilter, DateFilter, DateTimeFilter, TimeFilter, ModelChoiceFilter,
                      ModelMultipleChoiceFilter, NumberFilter, UUIDFilter)
from .utils import try_dbfield, get_model_field, resolve_field


ORDER_BY_FIELD = 'o'


class STRICTNESS(object):
    """
    Values of False & True chosen for backward compatability reasons.
    Originally, these were the only options.
    """
    IGNORE = False
    RETURN_NO_RESULTS = True
    RAISE_VALIDATION_ERROR = "RAISE"


def get_declared_filters(bases, attrs, with_base_filters=True):
    filters = []
    for filter_name, obj in list(attrs.items()):
        if isinstance(obj, Filter):
            obj = attrs.pop(filter_name)
            if getattr(obj, 'name', None) is None:
                obj.name = filter_name
            filters.append((filter_name, obj))
    filters.sort(key=lambda x: x[1].creation_counter)

    if with_base_filters:
        for base in bases[::-1]:
            if hasattr(base, 'base_filters'):
                filters = list(base.base_filters.items()) + filters
    else:
        for base in bases[::-1]:
            if hasattr(base, 'declared_filters'):
                filters = list(base.declared_filters.items()) + filters

    return OrderedDict(filters)


def filters_for_model(model, fields=None, exclude=None, filter_for_field=None,
                      filter_for_reverse_field=None):
    field_dict = OrderedDict()
    opts = model._meta
    if fields is None:
        fields = [f.name for f in sorted(opts.fields + opts.many_to_many)
                  if not isinstance(f, models.AutoField)]
    # Loop through the list of fields.
    for f in fields:
        # Skip the field if excluded.
        if exclude is not None and f in exclude:
            continue
        field = get_model_field(model, f)
        # Do nothing if the field doesn't exist.
        if field is None:
            field_dict[f] = None
            continue
        if isinstance(field, ForeignObjectRel):
            filter_ = filter_for_reverse_field(field, f)
            if filter_:
                field_dict[f] = filter_
        # If fields is a dictionary, it must contain lists.
        elif isinstance(fields, dict):
            # Create a filter for each lookup type.
            for lookup_expr in fields[f]:
                filter_ = filter_for_field(field, f, lookup_expr)

                if filter_:
                    filter_name = LOOKUP_SEP.join([f, lookup_expr])

                    # Don't add "exact" to filter names
                    _exact = LOOKUP_SEP + 'exact'
                    if filter_name.endswith(_exact):
                        filter_name = filter_name[:-len(_exact)]

                    field_dict[filter_name] = filter_
        # If fields is a list, it contains strings.
        else:
            filter_ = filter_for_field(field, f)
            if filter_:
                field_dict[f] = filter_
    return field_dict


def get_full_clean_override(together):
    def full_clean(form):

        def add_error(message):
            try:
                form.add_error(None, message)
            except AttributeError:
                form._errors[NON_FIELD_ERRORS] = message

        def all_valid(fieldset):
            cleaned_data = form.cleaned_data
            count = len([i for i in fieldset if cleaned_data.get(i)])
            return 0 < count < len(fieldset)

        super(form.__class__, form).full_clean()
        message = 'Following fields must be together: %s'
        if isinstance(together[0], (list, tuple)):
            for each in together:
                if all_valid(each):
                    return add_error(message % ','.join(each))
        elif all_valid(together):
            return add_error(message % ','.join(together))
    return full_clean


class FilterSetOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)

        self.order_by = getattr(options, 'order_by', False)

        self.form = getattr(options, 'form', forms.Form)

        self.together = getattr(options, 'together', None)


class FilterSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, FilterSet)]
        except NameError:
            # We are defining FilterSet itself here
            parents = None
        declared_filters = get_declared_filters(bases, attrs, False)
        new_class = super(
            FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)

        if not parents:
            return new_class

        opts = new_class._meta = FilterSetOptions(
            getattr(new_class, 'Meta', None))
        if opts.model:
            filters = filters_for_model(opts.model, opts.fields, opts.exclude,
                                        new_class.filter_for_field,
                                        new_class.filter_for_reverse_field)
            filters.update(declared_filters)
        else:
            filters = declared_filters

        not_defined = next((k for k, v in filters.items() if v is None), False)
        if not_defined:
            raise TypeError("Meta.fields contains a field that isn't defined "
                            "on this FilterSet: {}".format(not_defined))

        new_class.declared_filters = declared_filters
        new_class.base_filters = filters
        return new_class


FILTER_FOR_DBFIELD_DEFAULTS = {
    models.AutoField: {
        'filter_class': NumberFilter
    },
    models.CharField: {
        'filter_class': CharFilter
    },
    models.TextField: {
        'filter_class': CharFilter
    },
    models.BooleanField: {
        'filter_class': BooleanFilter
    },
    models.DateField: {
        'filter_class': DateFilter
    },
    models.DateTimeField: {
        'filter_class': DateTimeFilter
    },
    models.TimeField: {
        'filter_class': TimeFilter
    },
    models.OneToOneField: {
        'filter_class': ModelChoiceFilter,
        'extra': lambda f: {
            'queryset': remote_model(f)._default_manager.complex_filter(
                remote_field(f).limit_choices_to),
            'to_field_name': remote_field(f).field_name,
        }
    },
    models.ForeignKey: {
        'filter_class': ModelChoiceFilter,
        'extra': lambda f: {
            'queryset': remote_model(f)._default_manager.complex_filter(
                remote_field(f).limit_choices_to),
            'to_field_name': remote_field(f).field_name
        }
    },
    models.ManyToManyField: {
        'filter_class': ModelMultipleChoiceFilter,
        'extra': lambda f: {
            'queryset': remote_model(f)._default_manager.complex_filter(
                remote_field(f).limit_choices_to),
        }
    },
    models.DecimalField: {
        'filter_class': NumberFilter,
    },
    models.SmallIntegerField: {
        'filter_class': NumberFilter,
    },
    models.IntegerField: {
        'filter_class': NumberFilter,
    },
    models.PositiveIntegerField: {
        'filter_class': NumberFilter,
    },
    models.PositiveSmallIntegerField: {
        'filter_class': NumberFilter,
    },
    models.FloatField: {
        'filter_class': NumberFilter,
    },
    models.NullBooleanField: {
        'filter_class': BooleanFilter,
    },
    models.SlugField: {
        'filter_class': CharFilter,
    },
    models.EmailField: {
        'filter_class': CharFilter,
    },
    models.FilePathField: {
        'filter_class': CharFilter,
    },
    models.URLField: {
        'filter_class': CharFilter,
    },
    models.GenericIPAddressField: {
        'filter_class': CharFilter,
    },
    models.CommaSeparatedIntegerField: {
        'filter_class': CharFilter,
    },
    models.UUIDField: {
        'filter_class': UUIDFilter,
    },
}


class BaseFilterSet(object):
    filter_overrides = {}
    order_by_field = ORDER_BY_FIELD
    # What to do on on validation errors
    strict = STRICTNESS.RETURN_NO_RESULTS

    def __init__(self, data=None, queryset=None, prefix=None, strict=None):
        self.is_bound = data is not None
        self.data = data or {}
        if queryset is None:
            queryset = self._meta.model._default_manager.all()
        self.queryset = queryset
        self.form_prefix = prefix
        if strict is not None:
            self.strict = strict

        self.filters = copy.deepcopy(self.base_filters)
        # propagate the model being used through the filters
        for filter_ in self.filters.values():
            filter_.model = self._meta.model

        # Apply the parent to the filters, this will allow the filters to access the filterset
        for filter_key, filter_ in six.iteritems(self.filters):
            filter_.parent = self

    def __iter__(self):
        for obj in self.qs:
            yield obj

    def __len__(self):
        return self.qs.count()

    def __getitem__(self, key):
        return self.qs[key]

    @property
    def qs(self):
        if not hasattr(self, '_qs'):
            valid = self.is_bound and self.form.is_valid()

            if self.is_bound and not valid:
                if self.strict == STRICTNESS.RAISE_VALIDATION_ERROR:
                    raise forms.ValidationError(self.form.errors)
                elif bool(self.strict) == STRICTNESS.RETURN_NO_RESULTS:
                    self._qs = self.queryset.none()
                    return self._qs
                # else STRICTNESS.IGNORE...  ignoring

            # start with all the results and filter from there
            qs = self.queryset.all()
            for name, filter_ in six.iteritems(self.filters):
                value = None
                if valid:
                    value = self.form.cleaned_data[name]
                else:
                    raw_value = self.form[name].value()
                    try:
                        value = self.form.fields[name].clean(raw_value)
                    except forms.ValidationError:
                        if self.strict == STRICTNESS.RAISE_VALIDATION_ERROR:
                            raise
                        elif bool(self.strict) == STRICTNESS.RETURN_NO_RESULTS:
                            self._qs = self.queryset.none()
                            return self._qs
                        # else STRICTNESS.IGNORE...  ignoring

                if value is not None:  # valid & clean data
                    qs = filter_.filter(qs, value)

            if self._meta.order_by:
                order_field = self.form.fields[self.order_by_field]
                data = self.form[self.order_by_field].data
                ordered_value = None
                try:
                    ordered_value = order_field.clean(data)
                except forms.ValidationError:
                    pass

                # With a None-queryset, ordering must be enforced (#84).
                if (ordered_value in EMPTY_VALUES and
                        self.strict == STRICTNESS.RETURN_NO_RESULTS):
                    ordered_value = self.form.fields[self.order_by_field].choices[0][0]

                if ordered_value:
                    qs = qs.order_by(*self.get_order_by(ordered_value))

            self._qs = qs

        return self._qs

    def count(self):
        return self.qs.count()

    @property
    def form(self):
        if not hasattr(self, '_form'):
            fields = OrderedDict([
                (name, filter_.field)
                for name, filter_ in six.iteritems(self.filters)])
            fields[self.order_by_field] = self.ordering_field
            Form = type(str('%sForm' % self.__class__.__name__),
                        (self._meta.form,), fields)
            if self._meta.together:
                Form.full_clean = get_full_clean_override(self._meta.together)
            if self.is_bound:
                self._form = Form(self.data, prefix=self.form_prefix)
            else:
                self._form = Form(prefix=self.form_prefix)
        return self._form

    def get_ordering_field(self):
        if self._meta.order_by:
            if isinstance(self._meta.order_by, (list, tuple)):
                if isinstance(self._meta.order_by[0], (list, tuple)):
                    # e.g. (('field', 'Display name'), ...)
                    choices = [(f[0], f[1]) for f in self._meta.order_by]
                else:
                    choices = []
                    for f in self._meta.order_by:
                        if f[0] == '-':
                            label = _('%s (descending)' % capfirst(f[1:]))
                        else:
                            label = capfirst(f)
                        choices.append((f, label))
            else:
                # add asc and desc field names
                # use the filter's label if provided
                choices = []
                for f, fltr in self.filters.items():
                    choices.extend([
                        (f, fltr.label or capfirst(f)),
                        ("-%s" % (f), _('%s (descending)' % (fltr.label or capfirst(f))))
                    ])
            return forms.ChoiceField(label=_("Ordering"), required=False,
                                     choices=choices)

    @property
    def ordering_field(self):
        if not hasattr(self, '_ordering_field'):
            self._ordering_field = self.get_ordering_field()
        return self._ordering_field

    def get_order_by(self, order_choice):
        re_ordering_field = re.compile(r'(?P<inverse>\-?)(?P<field>.*)')
        m = re.match(re_ordering_field, order_choice)
        inverted = m.group('inverse')
        filter_api_name = m.group('field')

        _filter = self.filters.get(filter_api_name, None)

        if _filter and filter_api_name != _filter.name:
            return [inverted + _filter.name]
        return [order_choice]

    @classmethod
    def filter_for_field(cls, f, name, lookup_expr='exact'):
        f, lookup_type = resolve_field(f, lookup_expr)

        default = {
            'name': name,
            'label': capfirst(f.verbose_name),
            'lookup_expr': lookup_expr
        }

        filter_class, params = cls.filter_for_lookup(f, lookup_type)
        default.update(params)

        if filter_class is not None:
            return filter_class(**default)

    @classmethod
    def filter_for_reverse_field(cls, f, name):
        rel = remote_field(f.field)
        queryset = f.field.model._default_manager.all()
        default = {
            'name': name,
            'label': capfirst(rel.related_name),
            'queryset': queryset,
        }
        if rel.multiple:
            return ModelMultipleChoiceFilter(**default)
        else:
            return ModelChoiceFilter(**default)

    @classmethod
    def filter_for_lookup(cls, f, lookup_type):
        DEFAULTS = dict(FILTER_FOR_DBFIELD_DEFAULTS)
        DEFAULTS.update(cls.filter_overrides)

        data = try_dbfield(DEFAULTS.get, f.__class__) or {}
        filter_class = data.get('filter_class')
        params = data.get('extra', lambda f: {})(f)

        # if there is no filter class, exit early
        if not filter_class:
            return None, {}

        # perform lookup specific checks
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

        # Default behavior
        if f.choices:
            return ChoiceFilter, {'choices': f.choices}

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


def filterset_factory(model):
    meta = type(str('Meta'), (object,), {'model': model})
    filterset = type(str('%sFilterSet' % model._meta.object_name),
                     (FilterSet,), {'Meta': meta})
    return filterset
