from django import forms

from filter.widgets import RangeWidget

class RangeField(forms.MultiValueField):
    widget = RangeWidget
    
    def __init__(self, *args, **kwargs):
        fields = (
            forms.DecimalField(),
            forms.DecimalField(),
        )
        super(RangeField, self).__init__(fields, *args, **kwargs)
    
    def compress(self, data_list):
        if data_list:
            return slice(*data_list)
        return None
