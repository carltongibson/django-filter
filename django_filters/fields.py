from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime, time
from collections import namedtuple

from django import forms

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
        super(DateRangeField, self).__init__(*args, **kwargs)
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
        super(TimeRangeField, self).__init__(*args, **kwargs)
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
