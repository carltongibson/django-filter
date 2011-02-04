from django import forms

from django_filters.widgets import RangeWidget, LookupTypeWidget

class BaseRangeField(forms.MultiValueField):
    """
    Base abstract class for range filters. Inheriting classes must
    define form_field attribure which is a form field class to be used for
    validation.
    """
    widget = RangeWidget
    form_class = None
    def __init__(self, *args, **kwargs):
        fields = (
            self.form_class(),
            self.form_class(),
        )
        super(BaseRangeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return slice(*data_list)
        return None

class NumericRangeField(BaseRangeField):
    form_class = forms.DecimalField

class DateRangeField(BaseRangeField):
    form_class = forms.DateField

class TimeRangeField(BaseRangeField):
    form_class = forms.TimeField

class RangeField(forms.MultiValueField):
    """Deprecated. Use NumericRangeField instead."""
    form_class = forms.DecimalField
    
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
        return data_list