from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import patterns

from django_filters.views import FilterView
from .models import Book
from tests.filters import BookFilterSet


urlpatterns = patterns('',
    (r'^books-legacy/$',
        'django_filters.views.object_filter', {'model': Book}),
    (r'^books/$', FilterView.as_view(model=Book, filterset_class=BookFilterSet)),
)
