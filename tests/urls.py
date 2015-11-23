from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf.urls import url

from django_filters.views import FilterView, object_filter
from .models import Book


urlpatterns = [
    url(r'^books-legacy/$', object_filter, {'model': Book}),
    url(r'^books/$', FilterView.as_view(model=Book)),
]
