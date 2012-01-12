from django.conf.urls.defaults import *

from django_filters.tests.models import Book
from ..views import FilterView

urlpatterns = patterns('',
    (r'^books_functional/$', 'django_filters.views.object_filter', {'model': Book}),
    (r'^books_classbased/$', FilterView.as_view(model = Book)),
)
