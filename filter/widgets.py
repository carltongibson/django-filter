from itertools import chain
from urllib import urlencode

from django import forms
from django.forms.widgets import flatatt
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

class LinkWidget(forms.Widget):
    def __init__(self, attrs=None, choices=()):
        super(LinkWidget, self).__init__(attrs)
        
        self.choices = list(choices)
    
    def value_from_datadict(self, data, files, name):
        value = super(LinkWidget, self).value_from_datadict(data, files, name)
        self.data = data
        return value
        
    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs)
        output = [u'<ul%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, [value], name)
        if options:
            output.append(options)
        output.append('</ul>')
        return mark_safe(u'\n'.join(output))
    
    def render_options(self, choices, selected_choices, name):
        def render_option(option_value, option_label):
            option_value = force_unicode(option_value)
            data = self.data.copy()
            data[name] = option_value
            try:
                url = data.urlencode()
            except AttributeError:
                url = '?%s' % urlencode(data)
            return '<a href="%s">%s</a>' % (url, option_label)
        selected_choices = set(force_unicode(v) for v in selected_choices)
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                for option in option_label:
                    output.append(render_option(*option))
            else:
                output.append(render_option(option_value, option_label))
        return u'\n'.join(output)

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
