import warnings

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.utils import html

from django_filters.filterset import FilterSet, filterset_factory
from django_filters.views import FilterView

from .models import Book


@override_settings(ROOT_URLCONF='tests.urls')
class GenericViewTestCase(TestCase):

    def setUp(self):
        Book.objects.create(
            title="Ender's Game", price='1.00', average_rating=3.0)
        Book.objects.create(
            title="Rainbow Six", price='1.00', average_rating=3.0)
        Book.objects.create(
            title="Snowcrash", price='1.00', average_rating=3.0)


class GenericClassBasedViewTests(GenericViewTestCase):
    base_url = '/books/'

    def test_view(self):
        response = self.client.get(self.base_url)
        for b in ["Ender's Game", 'Rainbow Six', 'Snowcrash']:
            self.assertContains(response, html.escape(b))

    def test_view_filtering_on_title(self):
        response = self.client.get(self.base_url + '?title=Snowcrash')
        for b in ["Ender's Game", 'Rainbow Six']:
            self.assertNotContains(response, html.escape(b))
        self.assertContains(response, 'Snowcrash')

    def test_view_with_filterset_not_model(self):
        factory = RequestFactory()
        request = factory.get(self.base_url)
        filterset = filterset_factory(Book)
        view = FilterView.as_view(filterset_class=filterset)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        for b in ["Ender's Game", 'Rainbow Six', 'Snowcrash']:
            self.assertContains(response, html.escape(b))

    def test_view_with_model_no_filterset(self):
        factory = RequestFactory()
        request = factory.get(self.base_url)
        view = FilterView.as_view(model=Book)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        for b in ["Ender's Game", 'Rainbow Six', 'Snowcrash']:
            self.assertContains(response, html.escape(b))

    def test_view_with_model_and_fields_no_filterset(self):
        factory = RequestFactory()
        request = factory.get(self.base_url + '?price=1.0')
        view = FilterView.as_view(model=Book, filterset_fields=['price'])

        # filtering only by price
        response = view(request)
        self.assertEqual(response.status_code, 200)
        for b in ["Ender's Game", 'Rainbow Six', 'Snowcrash']:
            self.assertContains(response, html.escape(b))

        # not filtering by title
        request = factory.get(self.base_url + '?title=Snowcrash')
        response = view(request)
        self.assertEqual(response.status_code, 200)
        for b in ["Ender's Game", 'Rainbow Six', 'Snowcrash']:
            self.assertContains(response, html.escape(b))

    def test_view_with_strict_errors(self):
        factory = RequestFactory()
        request = factory.get(self.base_url + '?title=Snowcrash&price=four dollars')
        view = FilterView.as_view(model=Book)
        response = view(request)
        titles = [o.title for o in response.context_data['object_list']]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(titles, [])

    def test_view_with_non_strict_errors(self):
        factory = RequestFactory()
        request = factory.get(self.base_url + '?title=Snowcrash&price=four dollars')
        view = FilterView.as_view(model=Book, strict=False)
        response = view(request)
        titles = [o.title for o in response.context_data['object_list']]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(titles, ['Snowcrash'],)

    def test_view_without_filterset_or_model(self):
        factory = RequestFactory()
        request = factory.get(self.base_url)
        view = FilterView.as_view()
        with self.assertRaises(ImproperlyConfigured):
            view(request)

    def test_view_with_bad_filterset(self):
        class MyFilterSet(FilterSet):
            pass

        factory = RequestFactory()
        request = factory.get(self.base_url)
        view = FilterView.as_view(filterset_class=MyFilterSet)
        with self.assertRaises(ImproperlyConfigured):
            view(request)

    def test_filter_fields_removed(self):
        expected = "`View.filter_fields` attribute should be renamed `filterset_fields`. " \
                   "See: https://django-filter.readthedocs.io/en/master/guide/migration.html"
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter('always')

            class View(FilterView):
                filter_fields = None

        message = str(recorded.pop().message)
        self.assertEqual(message, expected)
        self.assertEqual(len(recorded), 0)

    def test_view_with_unbound_filter_form_returns_initial_queryset(self):
        factory = RequestFactory()
        request = factory.get(self.base_url)

        queryset = Book.objects.filter(title='Snowcrash')
        view = FilterView.as_view(model=Book, queryset=queryset)

        response = view(request)
        titles = [o.title for o in response.context_data['object_list']]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(titles, ['Snowcrash'])


class GenericFunctionalViewTests(GenericViewTestCase):
    base_url = '/books-legacy/'

    def test_view(self):
        response = self.client.get(self.base_url)
        for b in ["Ender's Game", 'Rainbow Six', 'Snowcrash']:
            self.assertContains(response, html.escape(b))
        # extra context
        self.assertEqual(response.context_data['foo'], 'bar')
        self.assertEqual(response.context_data['bar'], 'foo')

    def test_view_filtering_on_price(self):
        response = self.client.get(self.base_url + '?title=Snowcrash')
        for b in ["Ender's Game", 'Rainbow Six']:
            self.assertNotContains(response, html.escape(b))
        self.assertContains(response, 'Snowcrash')
