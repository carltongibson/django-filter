from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.views.generic import View
from django.views.generic.list import (
    MultipleObjectMixin,
    MultipleObjectTemplateResponseMixin,
    ListView)

from .constants import ALL_FIELDS
from .filterset import filterset_factory
from .utils import MigrationNotice, RenameAttributesBase


# TODO: remove metaclass in 2.1
class FilterMixinRenames(RenameAttributesBase):
    renamed_attributes = (
        ('filter_fields', 'filterset_fields', MigrationNotice),
    )


class FilterMixin(metaclass=FilterMixinRenames):
    """
    A mixin that provides a way to show and handle a FilterSet in a request.
    """
    filterset_class = None
    filterset_fields = ALL_FIELDS
    strict = True

    def get_filterset_class(self):
        """
        Returns the filterset class to use in this view
        """
        if self.filterset_class:
            return self.filterset_class
        elif self.model:
            return filterset_factory(model=self.model, fields=self.filterset_fields)
        else:
            msg = "'%s' must define 'filterset_class' or 'model'"
            raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_filterset(self, filterset_class):
        """
        Returns an instance of the filterset to be used in this view.
        """
        kwargs = self.get_filterset_kwargs(filterset_class)
        return filterset_class(**kwargs)

    def get_filterset_kwargs(self, filterset_class):
        """
        Returns the keyword arguments for instanciating the filterset.
        """
        kwargs = {
            'data': self.request.GET or None,
            'request': self.request,
        }
        try:
            kwargs.update({
                'queryset': self.get_queryset(),
            })
        except ImproperlyConfigured:
            # ignore the error here if the filterset has a model defined
            # to acquire a queryset from
            if filterset_class._meta.model is None:
                msg = ("'%s' does not define a 'model' and the view '%s' does "
                       "not return a valid queryset from 'get_queryset'.  You "
                       "must fix one of them.")
                args = (filterset_class.__name__, self.__class__.__name__)
                raise ImproperlyConfigured(msg % args)
        return kwargs

    def get_strict(self):
        return self.strict


class BaseFilterView(FilterMixin, MultipleObjectMixin, View):

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)

        if self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)
        return self.render_to_response(context)


class FilterView(MultipleObjectTemplateResponseMixin, BaseFilterView):
    """
    Render some list of objects with filter, set by `self.model` or
    `self.queryset`.
    `self.queryset` can actually be any iterable of items, not just a queryset.
    """
    template_name_suffix = '_filter'


def object_filter(request, model=None, queryset=None, template_name=None,
                  extra_context=None, context_processors=None,
                  filter_class=None):
    class ECFilterView(FilterView):
        """Handle the extra_context from the functional object_filter view"""
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            extra_context = self.kwargs.get('extra_context') or {}
            for k, v in extra_context.items():
                if callable(v):
                    v = v()
                context[k] = v
            return context

    kwargs = dict(model=model, queryset=queryset, template_name=template_name,
                  filterset_class=filter_class)
    view = ECFilterView.as_view(**kwargs)
    return view(request, extra_context=extra_context)


class FilterPaginatorView(ListView, FilterMixin):
    """
    A mixin that provides a way to handle a Filter and a Paginator in a ListView.
    """
    template_name_suffix = '_filter_paginator'

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        queryset = self.filterset.qs

        self.object_list = queryset
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = not self.object_list
            if is_empty:
                raise Http404(_("Empty list and '%(class_name)s.allow_empty' is False.") % {
                    'class_name': self.__class__.__name__,
                })

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)
        return self.render_to_response(context)
