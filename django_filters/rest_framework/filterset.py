from copy import deepcopy

from django.db import models
from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import Serializer

from django_filters import filterset

from .. import compat
from .filters import BooleanFilter, IsoDateTimeFilter

FILTER_FOR_DBFIELD_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
FILTER_FOR_DBFIELD_DEFAULTS.update({
    models.DateTimeField: {'filter_class': IsoDateTimeFilter},
    models.BooleanField: {'filter_class': BooleanFilter},
})


class FilterSetOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)

        self.filter_overrides = getattr(options, 'filter_overrides', {})

        self.form = getattr(options, 'form', Serializer)


class FilterSetMetaclass(filterset.FilterSetMetaclass):
    def __new__(cls, name, bases, attrs):
        attrs['declared_filters'] = cls.get_declared_filters(bases, attrs)

        new_class = type.__new__(cls, name, bases, attrs)
        new_class._meta = FilterSetOptions(getattr(new_class, 'Meta', None))
        new_class.base_filters = new_class.get_filters()

        return new_class


class FilterSet(filterset.BaseFilterSet, metaclass=FilterSetMetaclass):
    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS

    @property
    def form(self):
        if not hasattr(self, '_form'):
            Form = self.get_form_class()
            if self.is_bound:
                self._form = Form(data=self.data)
            else:
                self._form = Form()

        if compat.is_crispy():
            from crispy_forms.helper import FormHelper
            from crispy_forms.layout import Layout, Submit

            layout_components = list(form.fields.keys()) + [
                Submit('', _('Submit'), css_class='btn-default'),
            ]
            helper = FormHelper()
            helper.form_method = 'GET'
            helper.template_pack = 'bootstrap3'
            helper.layout = Layout(*layout_components)

            self._form.helper = helper

        return self._form

    def filter_queryset(self, queryset):
        for name, value in self.form.validated_data.items():
            queryset = self.filters[name].filter(queryset, value)
        return queryset
