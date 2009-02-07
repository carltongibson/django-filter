from django import forms

class RangeWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (forms.TextInput(attrs=attrs), forms.TextInput(attrs=attrs))
        super(RangeWidget, self).__init__(widgets, attrs)
    
    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return value
    
    def format_output(self, rendered_widgets):
        return u'-'.join(rendered_widgets)

class LookupTypeWidget(forms.MultiWidget):
    def decompress(self, value):
        return value
