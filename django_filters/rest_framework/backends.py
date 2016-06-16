
from __future__ import absolute_import

from django.conf import settings
from django.template import loader
from django.utils.translation import ugettext_lazy as _

from rest_framework import compat
from rest_framework.filters import BaseFilterBackend

from ..compat import crispy_forms
from . import filterset


if 'crispy_forms' in settings.INSTALLED_APPS and crispy_forms:
    from crispy_forms.helper import FormHelper
    from crispy_forms.layout import Layout, Submit

    class FilterSet(filterset.FilterSet):
        def __init__(self, *args, **kwargs):
            super(FilterSet, self).__init__(*args, **kwargs)
            for field in self.form.fields.values():
                field.help_text = None

            layout_components = list(self.form.fields.keys()) + [
                Submit('', _('Submit'), css_class='btn-default'),
            ]

            helper = FormHelper()
            helper.form_method = 'GET'
            helper.template_pack = 'bootstrap3'
            helper.layout = Layout(*layout_components)

            self.form.helper = helper

    filter_template = 'django_filters/rest_framework/crispy_form.html'

else:
    class FilterSet(filterset.FilterSet):
        def __init__(self, *args, **kwargs):
            super(FilterSet, self).__init__(*args, **kwargs)
            for field in self.form.fields.values():
                field.help_text = None

    filter_template = 'django_filters/rest_framework/form.html'


class FilterBackend(BaseFilterBackend):
    default_filter_set = FilterSet
    template = filter_template

    def get_filter_class(self, view, queryset=None):
        """
        Return the django-filters `FilterSet` used to filter the queryset.
        """
        filter_class = getattr(view, 'filter_class', None)
        filter_fields = getattr(view, 'filter_fields', None)

        if filter_class:
            filter_model = filter_class.Meta.model

            assert issubclass(queryset.model, filter_model), \
                'FilterSet model %s does not match queryset model %s' % \
                (filter_model, queryset.model)

            return filter_class

        if filter_fields:
            class AutoFilterSet(self.default_filter_set):
                class Meta:
                    model = queryset.model
                    fields = filter_fields

            return AutoFilterSet

        return None

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            return filter_class(request.query_params, queryset=queryset).qs

        return queryset

    def to_html(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)
        if not filter_class:
            return None
        filter_instance = filter_class(request.query_params, queryset=queryset)
        context = {
            'filter': filter_instance
        }
        template = loader.get_template(self.template)
        return compat.template_render(template, context)
