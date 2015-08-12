from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime, time
from collections import namedtuple

from django import forms
from django.utils.dateparse import parse_datetime

# TODO: Remove this once Django 1.4 is EOL.
try:
    from django.utils.encoding import force_str
except ImportError:
    force_str = None

from .widgets import RangeWidget, LookupTypeWidget


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
                start_date = datetime.combine(start_date, time.min)
            if stop_date:
                stop_date = datetime.combine(stop_date, time.max)
            return slice(start_date, stop_date)
        return None


class TimeRangeField(RangeField):

    def __init__(self, *args, **kwargs):
        fields = (
            forms.TimeField(),
            forms.TimeField())
        super(TimeRangeField, self).__init__(fields, *args, **kwargs)


Lookup = namedtuple('Lookup', ('value', 'lookup_type'))
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
        if len(data_list)==2:
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
        # TODO: Remove this once Django 1.4 is EOL.
        if force_str is not None:
            value = force_str(value)

        if format == self.ISO_8601:
            parsed = parse_datetime(value)
            if parsed is None:  # Continue with other formats if doesn't match
                raise ValueError
            return parsed
        return super(IsoDateTimeField, self).strptime(value, format)
