from __future__ import absolute_import
from __future__ import unicode_literals

import warnings
from collections import OrderedDict
from datetime import timedelta

from django import forms
from django.db.models import Q
from django.db.models.sql.constants import QUERY_TERMS
from django.db.models.constants import LOOKUP_SEP
from django.utils import six
from django.utils.itercompat import is_iterable
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from .conf import settings
from .fields import (
    Lookup, LookupTypeField, BaseCSVField, BaseRangeField, RangeField,
    DateRangeField, DateTimeRangeField, TimeRangeField, IsoDateTimeField
)
from .utils import deprecate, pretty_name


__all__ = [
    'AllValuesFilter',
    'BooleanFilter',
    'CharFilter',
    'ChoiceFilter',
    'DateFilter',
    'DateFromToRangeFilter',
    'DateRangeFilter',
    'DateTimeFilter',
    'DateTimeFromToRangeFilter',
    'DurationFilter',
    'Filter',
    'IsoDateTimeFilter',
    'MethodFilter',
    'ModelChoiceFilter',
    'ModelMultipleChoiceFilter',
    'MultipleChoiceFilter',
    'NumberFilter',
    'NumericRangeFilter',
    'OrderingFilter',
    'RangeFilter',
    'TimeFilter',
    'TimeRangeFilter',
    'TypedChoiceFilter',
    'UUIDFilter',
]


LOOKUP_TYPES = sorted(QUERY_TERMS)


EMPTY_VALUES = ([], (), {}, '', None)


def _lookup_type_warning():
    warnings.warn('lookup_type is deprecated. Use lookup_expr instead.', DeprecationWarning, stacklevel=3)


class Filter(object):
    creation_counter = 0
    field_class = forms.Field

    def __init__(self, name=None, label=None, widget=None, action=None, method=None,
                 lookup_expr='exact', required=False, distinct=False, exclude=False, **kwargs):
        self.name = name
        self.label = label
        if action:
            deprecate('Filter.action has been deprecated in favor of Filter.method')
            self.filter = action
        self.method = method

        self.lookup_expr = lookup_expr
        if 'lookup_type' in kwargs:
            _lookup_type_warning()
            self.lookup_expr = kwargs.pop('lookup_type')

        self.widget = widget
        self.required = required
        self.extra = kwargs
        self.distinct = distinct
        self.exclude = exclude

        self.creation_counter = Filter.creation_counter
        Filter.creation_counter += 1

    def get_method(self, qs):
        """Return filter method based on whether we're excluding
           or simply filtering.
        """
        return qs.exclude if self.exclude else qs.filter

    def method():
        """
        Filter method needs to be lazily resolved, as it may be dependent on
        the 'parent' FilterSet.
        """
        def fget(self):
            return self._method

        def fset(self, value):
            self._method = value

            # clear existing FilterMethod
            if isinstance(self.filter, FilterMethod):
                del self.filter

            # override filter w/ FilterMethod.
            if value is not None:
                self.filter = FilterMethod(self)

        return locals()
    method = property(**method())

    def lookup_type():
        def fget(self):
            _lookup_type_warning()
            return self.lookup_expr

        def fset(self, value):
            _lookup_type_warning()
            self.lookup_expr = value

        return locals()
    lookup_type = property(**lookup_type())

    @property
    def field(self):
        if not hasattr(self, '_field'):
            help_text = self.extra.pop('help_text', None)
            if help_text is None:
                if self.exclude and settings.HELP_TEXT_EXCLUDE:
                    help_text = _('This is an exclusion filter')
                elif not self.exclude and settings.HELP_TEXT_FILTER:
                    help_text = _('Filter')
                else:
                    help_text = ''

            if (self.lookup_expr is None or
                    isinstance(self.lookup_expr, (list, tuple))):

                lookup = []

                for x in LOOKUP_TYPES:
                    if isinstance(x, (list, tuple)) and len(x) == 2:
                        choice = (x[0], x[1])
                    else:
                        choice = (x, x)

                    if self.lookup_expr is None:
                        lookup.append(choice)
                    else:
                        if isinstance(x, (list, tuple)) and len(x) == 2:
                            if x[0] in self.lookup_expr:
                                lookup.append(choice)
                        else:
                            if x in self.lookup_expr:
                                lookup.append(choice)

                self._field = LookupTypeField(self.field_class(
                    required=self.required, widget=self.widget, **self.extra),
                    lookup, required=self.required, label=self.label, help_text=help_text)
            else:
                self._field = self.field_class(required=self.required,
                                               label=self.label, widget=self.widget,
                                               help_text=help_text, **self.extra)
        return self._field

    def filter(self, qs, value):
        if isinstance(value, Lookup):
            lookup = six.text_type(value.lookup_type)
            value = value.value
        else:
            lookup = self.lookup_expr
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        qs = self.get_method(qs)(**{'%s__%s' % (self.name, lookup): value})
        return qs


class CharFilter(Filter):
    field_class = forms.CharField


class BooleanFilter(Filter):
    field_class = forms.NullBooleanField


class ChoiceFilter(Filter):
    field_class = forms.ChoiceField


class TypedChoiceFilter(Filter):
    field_class = forms.TypedChoiceField


class UUIDFilter(Filter):
    field_class = forms.UUIDField


class MultipleChoiceFilter(Filter):
    """
    This filter performs OR(by default) or AND(using conjoined=True) query
    on the selected options.

    Advanced usage
    --------------
    Depending on your application logic, when all or no choices are selected,
    filtering may be a no-operation. In this case you may wish to avoid the
    filtering overhead, particularly if using a `distinct` call.

    You can override `get_filter_predicate` to use a custom filter.
    By default it will use the filter's name for the key, and the value will
    be the model object - or in case of passing in `to_field_name` the
    value of that attribute on the model.

    Set `always_filter` to `False` after instantiation to enable the default
    `is_noop` test. You can override `is_noop` if you need a different test
    for your application.

    `distinct` defaults to `True` on this class to preserve backward
    compatibility.
    """
    field_class = forms.MultipleChoiceField

    always_filter = True

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('distinct', True)
        self.conjoined = kwargs.pop('conjoined', False)
        super(MultipleChoiceFilter, self).__init__(*args, **kwargs)

    def is_noop(self, qs, value):
        """
        Return `True` to short-circuit unnecessary and potentially slow
        filtering.
        """
        if self.always_filter:
            return False

        # A reasonable default for being a noop...
        if self.required and len(value) == len(self.field.choices):
            return True

        return False

    def filter(self, qs, value):
        if not value:
            # Even though not a noop, no point filtering if empty.
            return qs

        if self.is_noop(qs, value):
            return qs

        if not self.conjoined:
            q = Q()
        for v in set(value):
            predicate = self.get_filter_predicate(v)
            if self.conjoined:
                qs = self.get_method(qs)(**predicate)
            else:
                q |= Q(**predicate)

        if not self.conjoined:
            qs = self.get_method(qs)(q)

        return qs.distinct() if self.distinct else qs

    def get_filter_predicate(self, v):
        try:
            return {self.name: getattr(v, self.field.to_field_name)}
        except (AttributeError, TypeError):
            return {self.name: v}


class DateFilter(Filter):
    field_class = forms.DateField


class DateTimeFilter(Filter):
    field_class = forms.DateTimeField


class IsoDateTimeFilter(DateTimeFilter):
    """
    Uses IsoDateTimeField to support filtering on ISO 8601 formated datetimes.

    For context see:

    * https://code.djangoproject.com/ticket/23448
    * https://github.com/tomchristie/django-rest-framework/issues/1338
    * https://github.com/alex/django-filter/pull/264
    """
    field_class = IsoDateTimeField


class TimeFilter(Filter):
    field_class = forms.TimeField


class DurationFilter(Filter):
    field_class = forms.DurationField


class ModelChoiceFilter(Filter):
    field_class = forms.ModelChoiceField


class ModelMultipleChoiceFilter(MultipleChoiceFilter):
    field_class = forms.ModelMultipleChoiceField


class NumberFilter(Filter):
    field_class = forms.DecimalField


class NumericRangeFilter(Filter):
    field_class = RangeField

    def filter(self, qs, value):
        if value:
            if value.start is not None and value.stop is not None:
                lookup = '%s__%s' % (self.name, self.lookup_expr)
                return self.get_method(qs)(**{lookup: (value.start, value.stop)})
            else:
                if value.start is not None:
                    qs = self.get_method(qs)(**{'%s__startswith' % self.name: value.start})
                if value.stop is not None:
                    qs = self.get_method(qs)(**{'%s__endswith' % self.name: value.stop})
            if self.distinct:
                qs = qs.distinct()
        return qs


class RangeFilter(Filter):
    field_class = RangeField

    def filter(self, qs, value):
        if value:
            if value.start is not None and value.stop is not None:
                lookup = '%s__range' % self.name
                return self.get_method(qs)(**{lookup: (value.start, value.stop)})
            else:
                if value.start is not None:
                    qs = self.get_method(qs)(**{'%s__gte' % self.name: value.start})
                if value.stop is not None:
                    qs = self.get_method(qs)(**{'%s__lte' % self.name: value.stop})
            if self.distinct:
                qs = qs.distinct()
        return qs


def _truncate(dt):
    return dt.date()


class DateRangeFilter(ChoiceFilter):
    options = {
        '': (_('Any date'), lambda qs, name: qs),
        1: (_('Today'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month,
            '%s__day' % name: now().day
        })),
        2: (_('Past 7 days'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: _truncate(now() - timedelta(days=7)),
            '%s__lt' % name: _truncate(now() + timedelta(days=1)),
        })),
        3: (_('This month'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month
        })),
        4: (_('This year'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
        })),
        5: (_('Yesterday'), lambda qs, name: qs.filter(**{
            '%s__year' % name: now().year,
            '%s__month' % name: now().month,
            '%s__day' % name: (now() - timedelta(days=1)).day,
        })),
    }

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [
            (key, value[0]) for key, value in six.iteritems(self.options)]
        super(DateRangeFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        try:
            value = int(value)
        except (ValueError, TypeError):
            value = ''

        assert value in self.options
        qs = self.options[value][1](qs, self.name)
        if self.distinct:
            qs = qs.distinct()
        return qs


class DateFromToRangeFilter(RangeFilter):
    field_class = DateRangeField


class DateTimeFromToRangeFilter(RangeFilter):
    field_class = DateTimeRangeField


class TimeRangeFilter(RangeFilter):
    field_class = TimeRangeField


class AllValuesFilter(ChoiceFilter):
    @property
    def field(self):
        qs = self.model._default_manager.distinct()
        qs = qs.order_by(self.name).values_list(self.name, flat=True)
        self.extra['choices'] = [(o, o) for o in qs]
        return super(AllValuesFilter, self).field


class AllValuesMultipleFilter(MultipleChoiceFilter):
    @property
    def field(self):
        qs = self.model._default_manager.distinct()
        qs = qs.order_by(self.name).values_list(self.name, flat=True)
        self.extra['choices'] = [(o, o) for o in qs]
        return super(AllValuesMultipleFilter, self).field


class BaseCSVFilter(Filter):
    """
    Base class for CSV type filters, such as IN and RANGE.
    """
    base_field_class = BaseCSVField

    def __init__(self, *args, **kwargs):
        super(BaseCSVFilter, self).__init__(*args, **kwargs)

        class ConcreteCSVField(self.base_field_class, self.field_class):
            pass
        ConcreteCSVField.__name__ = self._field_class_name(
            self.field_class, self.lookup_expr
        )

        self.field_class = ConcreteCSVField

    @classmethod
    def _field_class_name(cls, field_class, lookup_expr):
        """
        Generate a suitable class name for the concrete field class. This is not
        completely reliable, as not all field class names are of the format
        <Type>Field.

        ex::

            BaseCSVFilter._field_class_name(DateTimeField, 'year__in')

            returns 'DateTimeYearInField'

        """
        # DateTimeField => DateTime
        type_name = field_class.__name__
        if type_name.endswith('Field'):
            type_name = type_name[:-5]

        # year__in => YearIn
        parts = lookup_expr.split(LOOKUP_SEP)
        expression_name = ''.join(p.capitalize() for p in parts)

        # DateTimeYearInField
        return str('%s%sField' % (type_name, expression_name))


class BaseInFilter(BaseCSVFilter):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('lookup_expr', 'in')
        super(BaseInFilter, self).__init__(*args, **kwargs)


class BaseRangeFilter(BaseCSVFilter):
    base_field_class = BaseRangeField

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('lookup_expr', 'range')
        super(BaseRangeFilter, self).__init__(*args, **kwargs)


class OrderingFilter(BaseCSVFilter, ChoiceFilter):
    """
    Enable queryset ordering. As an extension of ``ChoiceFilter`` it accepts
    two additional arguments that are used to build the ordering choices.

    * ``fields`` is a mapping of {model field name: parameter name}. The
      parameter names are exposed in the choices and mask/alias the field
      names used in the ``order_by()`` call. Similar to field ``choices``,
      ``fields`` accepts the 'list of two-tuples' syntax that retains order.
      ``fields`` may also just be an iterable of strings. In this case, the
      field names simply double as the exposed parameter names.

    * ``field_labels`` is an optional argument that allows you to customize
      the display label for the corresponding parameter. It accepts a mapping
      of {field name: human readable label}. Keep in mind that the key is the
      field name, and not the exposed parameter name.

    Additionally, you can just provide your own ``choices`` if you require
    explicit control over the exposed options. For example, when you might
    want to disable descending sort options.

    This filter is also CSV-based, and accepts multiple ordering params. The
    default select widget does not enable the use of this, but it is useful
    for APIs.

    """
    descending_fmt = _('%s (descending)')

    def __init__(self, *args, **kwargs):
        """
        ``fields`` may be either a mapping or an iterable.
        ``field_labels`` must be a map of field names to display labels
        """
        fields = kwargs.pop('fields', {})
        fields = self.normalize_fields(fields)
        field_labels = kwargs.pop('field_labels', {})

        self.param_map = {v: k for k, v in fields.items()}

        if 'choices' not in kwargs:
            kwargs['choices'] = self.build_choices(fields, field_labels)

        kwargs.setdefault('label', _('Ordering'))
        super(OrderingFilter, self).__init__(*args, **kwargs)

    def get_ordering_value(self, param):
        descending = param.startswith('-')
        param = param[1:] if descending else param
        field_name = self.param_map.get(param, param)

        return "-%s" % field_name if descending else field_name

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        ordering = [self.get_ordering_value(param) for param in value]
        return qs.order_by(*ordering)

    @classmethod
    def normalize_fields(cls, fields):
        """
        Normalize the fields into an ordered map of {field name: param name}
        """
        # fields is a mapping, copy into new OrderedDict
        if isinstance(fields, dict):
            return OrderedDict(fields)

        # convert iterable of values => iterable of pairs (field name, param name)
        assert is_iterable(fields), \
            "'fields' must be an iterable (e.g., a list, tuple, or mapping)."

        # fields is an iterable of field names
        assert all(isinstance(field, six.string_types) or
                   is_iterable(field) and len(field) == 2  # may need to be wrapped in parens
                   for field in fields), \
            "'fields' must contain strings or (field name, param name) pairs."

        return OrderedDict([
            (f, f) if isinstance(f, six.string_types) else f for f in fields
        ])

    def build_choices(self, fields, labels):
        ascending = [
            (param, labels.get(field, pretty_name(param)))
            for field, param in fields.items()
        ]
        descending = [
            ('-%s' % pair[0], self.descending_fmt % pair[1])
            for pair in ascending
        ]

        # interleave the ascending and descending choices
        return [val for pair in zip(ascending, descending) for val in pair]


class MethodFilter(Filter):
    """
    This filter will allow you to run a method that exists on the filterset class
    """
    def __init__(self, *args, **kwargs):
        deprecate('MethodFilter has been deprecated in favor of Filter.method')

        # Get the action out of the kwargs
        action = kwargs.get('action', None)

        # If the action is a string store the action and set the action to our own filter method
        # so it can be backwards compatible and work as expected, the parent will still treat it as
        # a filter that has an action
        self.parent_action = ''
        text_types = (str, six.text_type)
        if type(action) in text_types:
            self.parent_action = str(action)
            kwargs.update({
                'action': self.filter
            })

        # Call the parent
        super(MethodFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):
        """
        This filter method will act as a proxy for the actual method we want to
        call.

        It will try to find the method on the parent filterset,
        if not it attempts to search for the method `field_{{attribute_name}}`.
        Otherwise it defaults to just returning the queryset.
        """
        parent = getattr(self, 'parent', None)
        parent_filter_method = getattr(parent, self.parent_action, None)
        if not parent_filter_method:
            func_str = 'filter_{0}'.format(self.name)
            parent_filter_method = getattr(parent, func_str, None)
        if parent_filter_method is not None:
            return parent_filter_method(qs, value)
        return qs


class FilterMethod(object):
    """
    This helper is used to override Filter.filter() when a 'method' argument
    is passed. It proxies the call to the actual method on the filter's parent.
    """
    def __init__(self, filter_instance):
        self.f = filter_instance

    def __call__(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        return self.method(qs, self.f.name, value)

    @property
    def method(self):
        """
        Resolve the method on the parent filterset.
        """
        instance = self.f

        # noop if 'method' is a function
        if callable(instance.method):
            return instance.method

        # otherwise, method is the name of a method on the parent FilterSet.
        assert hasattr(instance, 'parent'), \
            "Filter '%s' must have a parent FilterSet to find '.%s()'" %  \
            (instance.name, instance.method)

        parent = instance.parent
        method = getattr(parent, instance.method, None)

        assert callable(method), \
            "Expected parent FilterSet '%s.%s' to have a '.%s()' method." % \
            (parent.__class__.__module__, parent.__class__.__name__, instance.method)

        return method
