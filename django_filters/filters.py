from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import timedelta


from django import forms
from django.db.models import Q
from django.db.models.sql.constants import QUERY_TERMS
from django.utils import six
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from .fields import RangeField, LookupTypeField, Lookup


__all__ = [
    'Filter', 'CharFilter', 'BooleanFilter', 'ChoiceFilter',
    'MultipleChoiceFilter', 'DateFilter', 'DateTimeFilter', 'TimeFilter',
    'ModelChoiceFilter', 'ModelMultipleChoiceFilter', 'NumberFilter',
    'RangeFilter', 'DateRangeFilter', 'AllValuesFilter', 'MethodFilter'
]


LOOKUP_TYPES = sorted(QUERY_TERMS)


class Filter(object):
    creation_counter = 0
    field_class = forms.Field

    def __init__(self, name=None, label=None, widget=None, action=None,
        lookup_type='exact', required=False, distinct=False, exclude=False, **kwargs):
        self.name = name
        self.label = label
        if action:
            self.filter = action
        self.lookup_type = lookup_type
        self.widget = widget
        self.required = required
        self.extra = kwargs
        self.distinct = distinct
        self.exclude = exclude

        self.creation_counter = Filter.creation_counter
        Filter.creation_counter += 1

    @property
    def field(self):
        if not hasattr(self, '_field'):
            help_text = _('This is an exclusion filter') if self.exclude else ''
            if (self.lookup_type is None or
                    isinstance(self.lookup_type, (list, tuple))):
                if self.lookup_type is None:
                    lookup = [(x, x) for x in LOOKUP_TYPES]
                else:
                    lookup = [
                        (x, x) for x in LOOKUP_TYPES if x in self.lookup_type]
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
            lookup = self.lookup_type
        if value in ([], (), {}, None, ''):
            return qs
        method = qs.exclude if self.exclude else qs.filter
        qs = method(**{'%s__%s' % (self.name, lookup): value})
        if self.distinct:
            qs = qs.distinct()
        return qs


class CharFilter(Filter):
    field_class = forms.CharField


class BooleanFilter(Filter):
    field_class = forms.NullBooleanField

    def filter(self, qs, value):
        if value is not None:
            return qs.filter(**{self.name: value})
        return qs


class ChoiceFilter(Filter):
    field_class = forms.ChoiceField


class MultipleChoiceFilter(Filter):
    """
    This filter preforms an OR query on the selected options.
    """
    field_class = forms.MultipleChoiceField

    def filter(self, qs, value):
        value = value or ()
        if len(value) == len(self.field.choices):
            return qs
        q = Q()
        for v in value:
            q |= Q(**{self.name: v})
        return qs.filter(q).distinct()


class DateFilter(Filter):
    field_class = forms.DateField


class DateTimeFilter(Filter):
    field_class = forms.DateTimeField


class TimeFilter(Filter):
    field_class = forms.TimeField


class ModelChoiceFilter(Filter):
    field_class = forms.ModelChoiceField


class ModelMultipleChoiceFilter(MultipleChoiceFilter):
    field_class = forms.ModelMultipleChoiceField


class NumberFilter(Filter):
    field_class = forms.DecimalField


class RangeFilter(Filter):
    field_class = RangeField

    def filter(self, qs, value):
        if value:
            lookup = '%s__range' % self.name
            return qs.filter(**{lookup: (value.start, value.stop)})
        return qs


_truncate = lambda dt: dt.replace(hour=0, minute=0, second=0)


class DateRangeFilter(ChoiceFilter):
    options = {
        '': (_('Any date'), lambda qs, name: qs.all()),
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
        return self.options[value][1](qs, self.name)


class AllValuesFilter(ChoiceFilter):
    @property
    def field(self):
        qs = self.model._default_manager.distinct()
        qs = qs.order_by(self.name).values_list(self.name, flat=True)
        self.extra['choices'] = [(o, o) for o in qs]
        return super(AllValuesFilter, self).field


class MethodFilter(Filter):
    """
    This filter will allow you to run a method that exists on the filterset class
    """
    def __init__(self, *args, **kwargs):
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
        This filter method will act as a proxy for the actual method we want to call.
        It will try to find the method on the parent filterset, if not it defaults
        to just returning the queryset
        """
        parent = getattr(self, 'parent', None)
        parent_filter_method = getattr(parent, self.parent_action, None)
        if parent_filter_method is not None:
            return parent_filter_method(qs, value)
        return qs
