from __future__ import absolute_import
from __future__ import unicode_literals

from collections import Iterable
from itertools import chain
try:
    from urllib.parse import urlencode
except:
    from urllib import urlencode  # noqa

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms.widgets import flatatt
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.six import string_types
from django.utils.translation import ugettext as _

from .compat import format_value


class LinkWidget(forms.Widget):
    def __init__(self, attrs=None, choices=()):
        super(LinkWidget, self).__init__(attrs)

        self.choices = choices

    def value_from_datadict(self, data, files, name):
        value = super(LinkWidget, self).value_from_datadict(data, files, name)
        self.data = data
        return value

    def render(self, name, value, attrs=None, choices=()):
        if not hasattr(self, 'data'):
            self.data = {}
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs)
        output = ['<ul%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, [value], name)
        if options:
            output.append(options)
        output.append('</ul>')
        return mark_safe('\n'.join(output))

    def render_options(self, choices, selected_choices, name):
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                for option in option_label:
                    output.append(
                        self.render_option(name, selected_choices, *option))
            else:
                output.append(
                    self.render_option(name, selected_choices,
                                       option_value, option_label))
        return '\n'.join(output)

    def render_option(self, name, selected_choices,
                      option_value, option_label):
        option_value = force_text(option_value)
        if option_label == BLANK_CHOICE_DASH[0][1]:
            option_label = _("All")
        data = self.data.copy()
        data[name] = option_value
        selected = data == self.data or option_value in selected_choices
        try:
            url = data.urlencode()
        except AttributeError:
            url = urlencode(data)
        return self.option_string() % {
            'attrs': selected and ' class="selected"' or '',
            'query_string': url,
            'label': force_text(option_label)
        }

    def option_string(self):
        return '<li><a%(attrs)s href="?%(query_string)s">%(label)s</a></li>'


class RangeWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (forms.TextInput, forms.TextInput)
        super(RangeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def format_output(self, rendered_widgets):
        return '-'.join(rendered_widgets)


class LookupTypeWidget(forms.MultiWidget):
    def decompress(self, value):
        if value is None:
            return [None, None]
        return value


class BooleanWidget(forms.Select):
    """Convert true/false values into the internal Python True/False.
    This can be used for AJAX queries that pass true/false from JavaScript's
    internal types through.
    """
    def __init__(self, attrs=None):
        choices = (('', _('Unknown')),
                   ('true', _('Yes')),
                   ('false', _('No')))
        super(BooleanWidget, self).__init__(attrs, choices)

    def render(self, name, value, attrs=None):
        try:
            value = {
                True: 'true',
                False: 'false',
                '1': 'true',
                '0': 'false'
            }[value]
        except KeyError:
            value = ''
        return super(BooleanWidget, self).render(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        value = data.get(name, None)
        if isinstance(value, string_types):
            value = value.lower()

        return {
            '1': True,
            '0': False,
            'true': True,
            'false': False,
            True: True,
            False: False,
        }.get(value, None)


class BaseCSVWidget(forms.Widget):
    def _isiterable(self, value):
        return isinstance(value, Iterable) and not isinstance(value, string_types)

    def value_from_datadict(self, data, files, name):
        value = super(BaseCSVWidget, self).value_from_datadict(data, files, name)

        if value is not None:
            if value == '':  # empty value should parse as an empty list
                return []
            return value.split(',')
        return None

    def render(self, name, value, attrs=None):
        if not self._isiterable(value):
            value = [value]

        if len(value) <= 1:
            # delegate to main widget (Select, etc...) if not multiple values
            value = value[0] if value else value
            return super(BaseCSVWidget, self).render(name, value, attrs)

        # if we have multiple values, we need to force render as a text input
        # (otherwise, the additional values are lost)
        surrogate = forms.TextInput()
        value = [force_text(format_value(surrogate, v)) for v in value]
        value = ','.join(list(value))

        return surrogate.render(name, value, attrs)


class CSVWidget(BaseCSVWidget, forms.TextInput):
    pass
