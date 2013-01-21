# The patterns method moved in Django 1.4.
try:
    from django.conf.urls import patterns
except ImportError:
    from django.conf.urls.defaults import patterns

from django_filters.tests.models import Book
from django_filters.views import FilterView

urlpatterns = patterns('',
    (r'^books-legacy/$', 'django_filters.views.object_filter', {'model': Book}),
    (r'^books/$', FilterView.as_view(model=Book)),
)
