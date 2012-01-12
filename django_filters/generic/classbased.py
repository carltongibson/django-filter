#!/usr/bin/env python
# vim: set fileencoding=utf8:
"""
Class-based django-filter generic view


AUTHOR:
    lambdalisue[Ali su ae] (lambdalisue@hashnote.net)
    
Copyright:
    Copyright 2011 Alisue allright reserved.

License:
    Licensed under the Apache License, Version 2.0 (the "License"); 
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unliss required by applicable law or agreed to in writing, software
    distributed under the License is distrubuted on an "AS IS" BASICS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
__AUTHOR__ = "lambdalisue (lambdalisue@hashnote.net)"
from django.http import Http404
from django.views.generic import View
from django.views.generic.list import MultipleObjectMixin
from django.views.generic.list import MultipleObjectTemplateResponseMixin

from django_filters.filterset import FilterSet

class BaseFilterView(MultipleObjectMixin, View):
    filter_class = None

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(
                    _(u"Empty list and '%(class_name)s.allow empty' is "
                      u"False.") % {'class_name': self.__class__.__name__})
        context = self.get_context_data(request=request,
                                        object_list=self.object_list)
        return self.render_to_response(context)
    
    def get_filter_class(self):
        """get filter_class"""
        if self.filter_class:
            return self.filter_class
        elif self.model:
            meta = type(
                    'Meta', (object,), {'model': self.model})
            return type(
                    '%sFilterSet' % self.model._meta.object_name,
                    (FilterSet,), {'Meta': meta})
        else:
            raise TypeError(
                    u"""BaseFilterView must be used with either model or """
                    u"""filter_class""")

    def get_context_data(self, **kwargs):
        request = kwargs.pop('request')
        filter_class = self.get_filter_class()
        filterset = filter_class(request.GET or None, self.get_queryset())
        kwargs['filter'] = filterset
        return super(BaseFilterView, self).get_context_data(**kwargs)

class FilterView(MultipleObjectTemplateResponseMixin, BaseFilterView):
    """
    Render some list of objects with filter, set by `self.model` or
    `self.queryset`.
    `self.queryset` can actually be any iterable of items, not just a queryset.
    """
    template_name_suffix = '_filter'
