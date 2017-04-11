from __future__ import absolute_import, unicode_literals

from collections import Iterable
from itertools import chain
from re import search, sub

import django
from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms.utils import flatatt
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import force_text
from django.utils.http import urlencode
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
        if django.VERSION < (1, 11):
            final_attrs = self.build_attrs(attrs)
        else:
            final_attrs = self.build_attrs(self.attrs, extra_attrs=attrs)
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


class SuffixedMultiWidget(forms.MultiWidget):
    """
    A MultiWidget that allows users to provide custom suffixes instead of indexes.

    - Suffixes must be unique.
    - There must be the same number of suffixes as fields.
    """
    suffixes = []

    def __init__(self, *args, **kwargs):
        super(SuffixedMultiWidget, self).__init__(*args, **kwargs)

        assert len(self.widgets) == len(self.suffixes)
        assert len(self.suffixes) == len(set(self.suffixes))

    def suffixed(self, name, suffix):
        return '_'.join([name, suffix]) if suffix else name

    def get_context(self, name, value, attrs):
        context = super(SuffixedMultiWidget, self).get_context(name, value, attrs)
        for subcontext, suffix in zip(context['widget']['subwidgets'], self.suffixes):
            subcontext['name'] = self.suffixed(name, suffix)

        return context

    def value_from_datadict(self, data, files, name):
        return [
            widget.value_from_datadict(data, files, self.suffixed(name, suffix))
            for widget, suffix in zip(self.widgets, self.suffixes)
        ]

    def value_omitted_from_data(self, data, files, name):
        return all(
            widget.value_omitted_from_data(data, files, self.suffixed(name, suffix))
            for widget, suffix in zip(self.widgets, self.suffixes)
        )

    # Django < 1.11 compat
    def format_output(self, rendered_widgets):
        rendered_widgets = [
            self.replace_name(output, i)
            for i, output in enumerate(rendered_widgets)
        ]
        return '\n'.join(rendered_widgets)

    def replace_name(self, output, index):
        result = search(r'name="(?P<name>.*)_%d"' % index, output)
        name = result.group('name')
        name = self.suffixed(name, self.suffixes[index])
        name = 'name="%s"' % name

        return sub(r'name=".*_%d"' % index, name, output)

    def decompress(self, value):
        if value is None:
            return [None, None]
        return value


class RangeWidget(forms.MultiWidget):
    template_name = 'django_filters/widgets/multiwidget.html'

    def __init__(self, attrs=None):
        widgets = (forms.TextInput, forms.TextInput)
        super(RangeWidget, self).__init__(widgets, attrs)

    def format_output(self, rendered_widgets):
        # Method was removed in Django 1.11.
        return '-'.join(rendered_widgets)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]


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
            value = value[0] if value else ''
            return super(BaseCSVWidget, self).render(name, value, attrs)

        # if we have multiple values, we need to force render as a text input
        # (otherwise, the additional values are lost)
        surrogate = forms.TextInput()
        value = [force_text(format_value(surrogate, v)) for v in value]
        value = ','.join(list(value))

        return surrogate.render(name, value, attrs)


class CSVWidget(BaseCSVWidget, forms.TextInput):
    pass


class QueryArrayWidget(BaseCSVWidget, forms.TextInput):
    """
    Enables request query array notation that might be consumed by MultipleChoiceFilter

    1. Values can be provided as csv string:  ?foo=bar,baz
    2. Values can be provided as query array: ?foo[]=bar&foo[]=baz
    3. Values can be provided as query array: ?foo=bar&foo=baz

    Note: Duplicate and empty values are skipped from results
    """

    def value_from_datadict(self, data, files, name):
        if not isinstance(data, MultiValueDict):
            for key, value in data.items():
                # treat value as csv string: ?foo=1,2
                if isinstance(value, string_types):
                    data[key] = [x.strip() for x in value.rstrip(',').split(',') if x]
            data = MultiValueDict(data)

        values_list = data.getlist(name, data.getlist('%s[]' % name)) or []

        # apparently its an array, so no need to process it's values as csv
        # ?foo=1&foo=2 -> data.getlist(foo) -> foo = [1, 2]
        # ?foo[]=1&foo[]=2 -> data.getlist(foo[]) -> foo = [1, 2]
        if len(values_list) > 0:
            ret = [x for x in values_list if x]
        else:
            ret = []

        return list(set(ret))
