
from __future__ import absolute_import

from django.template import loader
from rest_framework.filters import BaseFilterBackend

from .. import compat
from . import filterset


if compat.is_crispy:
    filter_template = 'django_filters/rest_framework/crispy_form.html'
else:
    filter_template = 'django_filters/rest_framework/form.html'


class DjangoFilterBackend(BaseFilterBackend):
    default_filter_set = filterset.FilterSet
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
