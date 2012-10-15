# The patterns method moved in Django 1.4.
try:
    from django.conf.urls import patterns
except ImportError:
    from django.conf.urls.defaults import patterns

from django_filters.tests.models import Book

urlpatterns = patterns('',
    (r'^books/$', 'django_filters.views.object_filter', {'model': Book}),
)
