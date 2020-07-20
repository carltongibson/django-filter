from django.urls import path

from django_filters.views import FilterView, object_filter

from .models import Book


def _foo():
    return 'bar'


urlpatterns = [
    path('books-legacy/', object_filter, {'model': Book, 'extra_context': {'foo': _foo, 'bar': 'foo'}}),
    path('books/', FilterView.as_view(model=Book)),
]
