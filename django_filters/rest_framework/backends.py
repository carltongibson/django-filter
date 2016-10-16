
from __future__ import absolute_import

from django.template import Template, TemplateDoesNotExist, loader
from rest_framework.compat import template_render
from rest_framework.filters import BaseFilterBackend

from .. import compat
from . import filterset


CRISPY_TEMPLATE = """
{% load crispy_forms_tags %}
{% load i18n %}

<h2>{% trans "Field filters" %}</h2>
{% crispy filter.form %}
"""


FILTER_TEMPLATE = """
{% load i18n %}
<h2>{% trans "Field filters" %}</h2>
<form class="form" action="" method="get">
    {{ filter.form.as_p }}
    <button type="submit" class="btn btn-primary">{% trans "Submit" %}</button>
</form>
"""


if compat.is_crispy:
    template_path = 'django_filters/rest_framework/crispy_form.html'
    template_default = CRISPY_TEMPLATE

else:
    template_path = 'django_filters/rest_framework/form.html'
    template_default = FILTER_TEMPLATE


class DjangoFilterBackend(BaseFilterBackend):
    default_filter_set = filterset.FilterSet
    template = template_path

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

        try:
            template = loader.get_template(self.template)
        except TemplateDoesNotExist:
            template = Template(template_default)

        return template_render(template, context={
            'filter': filter_instance
        })

    def get_schema_fields(self, view):
        # This is not compatible with widgets where the query param differs from the
        # filter's attribute name. Notably, this includes `MultiWidget`, where query
        # params will be of the format `<name>_0`, `<name>_1`, etc...
        assert compat.coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        filter_class = self.get_filter_class(view, view.get_queryset())

        return [] if not filter_class else [
            compat.coreapi.Field(name=field_name, required=False, location='query')
            for field_name in filter_class().filters.keys()
        ]
