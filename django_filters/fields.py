from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime, time
from collections import namedtuple

from django import forms
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from django.utils.encoding import force_str

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
    default_timezone = timezone.get_default_timezone() if settings.USE_TZ else None

    def strptime(self, value, format):
        value = force_str(value)

        if format == self.ISO_8601:
            parsed = parse_datetime(value)
            if parsed is None:  # Continue with other formats if doesn't match
                raise ValueError

            # Handle timezone awareness. Copied from:
            # https://github.com/tomchristie/django-rest-framework/blob/3.2.0/rest_framework/fields.py#L965-L969
            if settings.USE_TZ and not timezone.is_aware(parsed):
                return timezone.make_aware(parsed, self.default_timezone)
            elif not settings.USE_TZ and timezone.is_aware(parsed):
                return timezone.make_naive(parsed, timezone.UTC())
            return parsed
        return super(IsoDateTimeField, self).strptime(value, format)
