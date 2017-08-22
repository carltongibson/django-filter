from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from django_filters.views import FilterView, object_filter

from .models import Book


def _foo():
    return 'bar'

urlpatterns = [
    url(r'^books-legacy/$', object_filter, {'model': Book, 'extra_context': {'foo': _foo, 'bar': 'foo'}}),
    url(r'^books/$', FilterView.as_view(model=Book)),
]
