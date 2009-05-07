from django.conf.urls.defaults import *

from filter.models import Book

urlpatterns = patterns('',
    (r'^books/$', 'filter.views.object_filter', {'model': Book}),
)
