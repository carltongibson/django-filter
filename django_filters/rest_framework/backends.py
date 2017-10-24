import warnings

from django.template import loader

from . import filters, filterset
from .. import compat, utils


class DjangoFilterBackend(object):
    default_filter_set = filterset.FilterSet
    raise_exception = True

    @property
    def template(self):
        if compat.is_crispy():
            return 'django_filters/rest_framework/crispy_form.html'
        return 'django_filters/rest_framework/form.html'

    def get_filter_class(self, view, queryset=None):
        """
        Return the django-filters `FilterSet` used to filter the queryset.
        """
        filter_class = getattr(view, 'filter_class', None)
        filter_fields = getattr(view, 'filter_fields', None)

        if filter_class:
            filter_model = filter_class._meta.model

            # FilterSets do not need to specify a Meta class
            if filter_model and queryset is not None:
                assert issubclass(queryset.model, filter_model), \
                    'FilterSet model %s does not match queryset model %s' % \
                    (filter_model, queryset.model)

            return filter_class

        if filter_fields and queryset is not None:
            MetaBase = getattr(self.default_filter_set, 'Meta', object)

            class AutoFilterSet(self.default_filter_set):
                class Meta(MetaBase):
                    model = queryset.model
                    fields = filter_fields

            return AutoFilterSet

        return None

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            filterset = filter_class(request.query_params, queryset=queryset, request=request)
            if not filterset.is_valid() and self.raise_exception:
                raise utils.translate_validation(filterset.errors)
            return filterset.qs
        return queryset

    def to_html(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)
        if not filter_class:
            return None
        filter_instance = filter_class(request.query_params, queryset=queryset, request=request)

        template = loader.get_template(self.template)
        context = {
            'filter': filter_instance
        }

        return template.render(context, request)

    def get_coreschema_field(self, field):
        if isinstance(field, filters.NumberFilter):
            field_cls = compat.coreschema.Number
        else:
            field_cls = compat.coreschema.String
        return field_cls(
            description=str(field.extra.get('help_text', ''))
        )

    def get_schema_fields(self, view):
        # This is not compatible with widgets where the query param differs from the
        # filter's attribute name. Notably, this includes `MultiWidget`, where query
        # params will be of the format `<name>_0`, `<name>_1`, etc...
        assert compat.coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert compat.coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'

        try:
            queryset = view.get_queryset()
        except Exception:
            queryset = None
            warnings.warn(
                "{} is not compatible with schema generation".format(view.__class__)
            )

        filter_class = self.get_filter_class(view, queryset)

        return [] if not filter_class else [
            compat.coreapi.Field(
                name=field_name,
                required=field.extra['required'],
                location='query',
                schema=self.get_coreschema_field(field)
            ) for field_name, field in filter_class.base_filters.items()
        ]
