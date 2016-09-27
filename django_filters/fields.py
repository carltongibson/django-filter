from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime, time
from collections import namedtuple

from django import forms
from django.utils.dateparse import parse_datetime

from django.utils.encoding import force_str
from django.utils.translation import ugettext_lazy as _

from .utils import handle_timezone
from .widgets import RangeWidget, LookupTypeWidget, CSVWidget, BaseCSVWidget


class RangeField(forms.MultiValueField):
    widget = RangeWidget

    def __init__(self, fields=None, *args, **kwargs):
        if fields is None:
            fields = (
                forms.DecimalField(),
                forms.DecimalField())
        super(RangeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return slice(*data_list)
        return None


class DateRangeField(RangeField):

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateField(),
            forms.DateField())
        super(DateRangeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            start_date, stop_date = data_list
            if start_date:
                start_date = handle_timezone(
                    datetime.combine(start_date, time.min))
            if stop_date:
                stop_date = handle_timezone(
                    datetime.combine(stop_date, time.max))
            return slice(start_date, stop_date)
        return None


class DateTimeRangeField(RangeField):

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateTimeField(),
            forms.DateTimeField())
        super(DateTimeRangeField, self).__init__(fields, *args, **kwargs)


class TimeRangeField(RangeField):

    def __init__(self, *args, **kwargs):
        fields = (
            forms.TimeField(),
            forms.TimeField())
        super(TimeRangeField, self).__init__(fields, *args, **kwargs)


class Lookup(namedtuple('Lookup', ('value', 'lookup_type'))):
    # python nature is test __len__ on tuple types for boolean check
    def __len__(self):
        if not self.value:
            return 0
        return 2


class LookupTypeField(forms.MultiValueField):
    def __init__(self, field, lookup_choices, *args, **kwargs):
        fields = (
            field,
            forms.ChoiceField(choices=lookup_choices)
        )
        defaults = {
            'widgets': [f.widget for f in fields],
        }
        widget = LookupTypeWidget(**defaults)
        kwargs['widget'] = widget
        super(LookupTypeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if len(data_list) == 2:
            return Lookup(value=data_list[0], lookup_type=data_list[1] or 'exact')
        return Lookup(value=None, lookup_type='exact')


class IsoDateTimeField(forms.DateTimeField):
    """
    Supports 'iso-8601' date format too which is out the scope of
    the ``datetime.strptime`` standard library

    # ISO 8601: ``http://www.w3.org/TR/NOTE-datetime``

    Based on Gist example by David Medina https://gist.github.com/copitux/5773821
    """
    ISO_8601 = 'iso-8601'
    input_formats = [ISO_8601]

    def strptime(self, value, format):
        value = force_str(value)

        if format == self.ISO_8601:
            parsed = parse_datetime(value)
            if parsed is None:  # Continue with other formats if doesn't match
                raise ValueError
            return handle_timezone(parsed)
        return super(IsoDateTimeField, self).strptime(value, format)


class BaseCSVField(forms.Field):
    """
    Base field for validating CSV types. Value validation is performed by
    secondary base classes.

    ex::
        class IntegerCSVField(BaseCSVField, filters.IntegerField):
            pass

    """
    base_widget_class = BaseCSVWidget

    def __init__(self, *args, **kwargs):
        widget = kwargs.get('widget') or self.widget
        kwargs['widget'] = self._get_widget_class(widget)

        super(BaseCSVField, self).__init__(*args, **kwargs)

    def _get_widget_class(self, widget):
        # passthrough, allows for override
        if isinstance(widget, BaseCSVWidget) or (
                isinstance(widget, type) and
                issubclass(widget, BaseCSVWidget)):
            return widget

        # complain since we are unable to reconstruct widget instances
        assert isinstance(widget, type), \
            "'%s.widget' must be a widget class, not %s." \
            % (self.__class__.__name__, repr(widget))

        bases = (self.base_widget_class, widget, )
        return type(str('CSV%s' % widget.__name__), bases, {})

    def clean(self, value):
        if value is None:
            return None
        return [super(BaseCSVField, self).clean(v) for v in value]


class BaseRangeField(BaseCSVField):
    # Force use of text input, as range must always have two inputs. A date
    # input would only allow a user to input one value and would always fail.
    widget = CSVWidget

    default_error_messages = {
        'invalid_values': _('Range query expects two values.')
    }

    def clean(self, value):
        value = super(BaseRangeField, self).clean(value)

        if value is not None and len(value) != 2:
            raise forms.ValidationError(
                self.error_messages['invalid_values'],
                code='invalid_values')

        return value
