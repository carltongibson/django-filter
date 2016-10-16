from __future__ import unicode_literals

import datetime
from decimal import Decimal
from unittest import skipIf

from django.conf.urls import url
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.dateparse import parse_date

try:
    from django.urls import reverse
except ImportError:
    # Django < 1.10 compatibility
    from django.core.urlresolvers import reverse

from rest_framework import generics, serializers, status
from rest_framework.test import APIRequestFactory

from django_filters import compat, filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters.rest_framework import backends

from .models import BaseFilterableItem, BasicModel, FilterableItem, DjangoFilterOrderingModel

factory = APIRequestFactory()


class FilterableItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterableItem
        fields = '__all__'


# Basic filter on a list view.
class FilterFieldsRootView(generics.ListCreateAPIView):
    queryset = FilterableItem.objects.all()
    serializer_class = FilterableItemSerializer
    filter_fields = ['decimal', 'date']
    filter_backends = (DjangoFilterBackend,)


# These class are used to test a filter class.
class SeveralFieldsFilter(FilterSet):
    text = filters.CharFilter(lookup_expr='icontains')
    decimal = filters.NumberFilter(lookup_expr='lt')
    date = filters.DateFilter(lookup_expr='gt')

    class Meta:
        model = FilterableItem
        fields = ['text', 'decimal', 'date']


class FilterClassRootView(generics.ListCreateAPIView):
    queryset = FilterableItem.objects.all()
    serializer_class = FilterableItemSerializer
    filter_class = SeveralFieldsFilter
    filter_backends = (DjangoFilterBackend,)


# These classes are used to test a misconfigured filter class.
class MisconfiguredFilter(FilterSet):
    text = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = BasicModel
        fields = ['text']


class IncorrectlyConfiguredRootView(generics.ListCreateAPIView):
    queryset = FilterableItem.objects.all()
    serializer_class = FilterableItemSerializer
    filter_class = MisconfiguredFilter
    filter_backends = (DjangoFilterBackend,)


class FilterClassDetailView(generics.RetrieveAPIView):
    queryset = FilterableItem.objects.all()
    serializer_class = FilterableItemSerializer
    filter_class = SeveralFieldsFilter
    filter_backends = (DjangoFilterBackend,)


# These classes are used to test base model filter support
class BaseFilterableItemFilter(FilterSet):
    text = filters.CharFilter()

    class Meta:
        model = BaseFilterableItem
        fields = '__all__'


class BaseFilterableItemFilterRootView(generics.ListCreateAPIView):
    queryset = FilterableItem.objects.all()
    serializer_class = FilterableItemSerializer
    filter_class = BaseFilterableItemFilter
    filter_backends = (DjangoFilterBackend,)


# Regression test for #814
class FilterFieldsQuerysetView(generics.ListCreateAPIView):
    queryset = FilterableItem.objects.all()
    serializer_class = FilterableItemSerializer
    filter_fields = ['decimal', 'date']
    filter_backends = (DjangoFilterBackend,)


class GetQuerysetView(generics.ListCreateAPIView):
    serializer_class = FilterableItemSerializer
    filter_class = SeveralFieldsFilter
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        return FilterableItem.objects.all()


urlpatterns = [
    url(r'^(?P<pk>\d+)/$', FilterClassDetailView.as_view(), name='detail-view'),
    url(r'^$', FilterClassRootView.as_view(), name='root-view'),
    url(r'^get-queryset/$', GetQuerysetView.as_view(), name='get-queryset-view'),
]


@skipIf(compat.coreapi is None, 'coreapi must be installed')
class GetSchemaFieldsTests(TestCase):
    def test_fields_with_filter_fields_list(self):
        backend = DjangoFilterBackend()
        fields = backend.get_schema_fields(FilterFieldsRootView())
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['decimal', 'date'])

    def test_fields_with_filter_fields_dict(self):
        class DictFilterFieldsRootView(FilterFieldsRootView):
            filter_fields = {
                'decimal': ['exact', 'lt', 'gt'],
            }

        backend = DjangoFilterBackend()
        fields = backend.get_schema_fields(DictFilterFieldsRootView())
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['decimal', 'decimal__lt', 'decimal__gt'])

    def test_fields_with_filter_class(self):
        backend = DjangoFilterBackend()
        fields = backend.get_schema_fields(FilterClassRootView())
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['text', 'decimal', 'date'])


class CommonFilteringTestCase(TestCase):
    def _serialize_object(self, obj):
        return {'id': obj.id, 'text': obj.text, 'decimal': str(obj.decimal), 'date': obj.date.isoformat()}

    def setUp(self):
        """
        Create 10 FilterableItem instances.
        """
        base_data = ('a', Decimal('0.25'), datetime.date(2012, 10, 8))
        for i in range(10):
            text = chr(i + ord(base_data[0])) * 3  # Produces string 'aaa', 'bbb', etc.
            decimal = base_data[1] + i
            date = base_data[2] - datetime.timedelta(days=i * 2)
            FilterableItem(text=text, decimal=decimal, date=date).save()

        self.objects = FilterableItem.objects
        self.data = [
            self._serialize_object(obj)
            for obj in self.objects.all()
        ]


class IntegrationTestFiltering(CommonFilteringTestCase):
    """
    Integration tests for filtered list views.
    """

    def test_get_filtered_fields_root_view(self):
        """
        GET requests to paginated ListCreateAPIView should return paginated results.
        """
        view = FilterFieldsRootView.as_view()

        # Basic test with no filter.
        request = factory.get('/')
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

        # Tests that the decimal filter works.
        search_decimal = Decimal('2.25')
        request = factory.get('/', {'decimal': '%s' % search_decimal})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if Decimal(f['decimal']) == search_decimal]
        self.assertEqual(response.data, expected_data)

        # Tests that the date filter works.
        search_date = datetime.date(2012, 9, 22)
        request = factory.get('/', {'date': '%s' % search_date})  # search_date str: '2012-09-22'
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if parse_date(f['date']) == search_date]
        self.assertEqual(response.data, expected_data)

    def test_filter_with_queryset(self):
        """
        Regression test for #814.
        """
        view = FilterFieldsQuerysetView.as_view()

        # Tests that the decimal filter works.
        search_decimal = Decimal('2.25')
        request = factory.get('/', {'decimal': '%s' % search_decimal})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if Decimal(f['decimal']) == search_decimal]
        self.assertEqual(response.data, expected_data)

    def test_filter_with_get_queryset_only(self):
        """
        Regression test for #834.
        """
        view = GetQuerysetView.as_view()
        request = factory.get('/get-queryset/')
        view(request).render()
        # Used to raise "issubclass() arg 2 must be a class or tuple of classes"
        # here when neither `model' nor `queryset' was specified.

    def test_get_filtered_class_root_view(self):
        """
        GET requests to filtered ListCreateAPIView that have a filter_class set
        should return filtered results.
        """
        view = FilterClassRootView.as_view()

        # Basic test with no filter.
        request = factory.get('/')
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

        # Tests that the decimal filter set with 'lt' in the filter class works.
        search_decimal = Decimal('4.25')
        request = factory.get('/', {'decimal': '%s' % search_decimal})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if Decimal(f['decimal']) < search_decimal]
        self.assertEqual(response.data, expected_data)

        # Tests that the date filter set with 'gt' in the filter class works.
        search_date = datetime.date(2012, 10, 2)
        request = factory.get('/', {'date': '%s' % search_date})  # search_date str: '2012-10-02'
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if parse_date(f['date']) > search_date]
        self.assertEqual(response.data, expected_data)

        # Tests that the text filter set with 'icontains' in the filter class works.
        search_text = 'ff'
        request = factory.get('/', {'text': '%s' % search_text})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if search_text in f['text'].lower()]
        self.assertEqual(response.data, expected_data)

        # Tests that multiple filters works.
        search_decimal = Decimal('5.25')
        search_date = datetime.date(2012, 10, 2)
        request = factory.get('/', {
            'decimal': '%s' % (search_decimal,),
            'date': '%s' % (search_date,)
        })
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if parse_date(f['date']) > search_date and
                         Decimal(f['decimal']) < search_decimal]
        self.assertEqual(response.data, expected_data)

    def test_incorrectly_configured_filter(self):
        """
        An error should be displayed when the filter class is misconfigured.
        """
        view = IncorrectlyConfiguredRootView.as_view()

        request = factory.get('/')
        self.assertRaises(AssertionError, view, request)

    def test_base_model_filter(self):
        """
        The `get_filter_class` model checks should allow base model filters.
        """
        view = BaseFilterableItemFilterRootView.as_view()

        request = factory.get('/?text=aaa')
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unknown_filter(self):
        """
        GET requests with filters that aren't configured should return 200.
        """
        view = FilterFieldsRootView.as_view()

        search_integer = 10
        request = factory.get('/', {'integer': '%s' % search_integer})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_html_rendering(self):
        """
        Make sure response renders w/ backend
        """
        view = FilterFieldsRootView.as_view()
        request = factory.get('/')
        request.META['HTTP_ACCEPT'] = 'text/html'
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_backend_output(self):
        """
        Ensure backend renders default if template path does not exist
        """
        view = FilterFieldsRootView()
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get('/'))
        html = backend().to_html(request, view.get_queryset(), view)

        self.assertHTMLEqual(html, """
        <h2>Field filters</h2>
        <form class="form" action="" method="get">
            <p>
                <label for="id_decimal">Decimal:</label>
                <input id="id_decimal" name="decimal" step="any" type="number" />
                <span class="helptext">Filter</span>
            </p>
            <p>
                <label for="id_date">Date:</label>
                <input id="id_date" name="date" type="text" />
                <span class="helptext">Filter</span>
            </p>
            <button type="submit" class="btn btn-primary">Submit</button>
        </form>
        """)

    def test_template_path(self):
        view = FilterFieldsRootView()

        class Backend(view.filter_backends[0]):
            template = 'filter_template.html'

        request = view.initialize_request(factory.get('/'))
        html = Backend().to_html(request, view.get_queryset(), view)

        self.assertHTMLEqual(html, "Test")

    @override_settings(TEMPLATES=[])
    def test_DTL_missing(self):
        # The backend should be importable even if the DTL is not used.
        # See: https://github.com/carltongibson/django-filter/issues/506
        try:
            from importlib import reload  # python 3.4
        except ImportError:
            from imp import reload

        reload(backends)


@override_settings(ROOT_URLCONF='tests.rest_framework.test_backends')
class IntegrationTestDetailFiltering(CommonFilteringTestCase):
    """
    Integration tests for filtered detail views.
    """
    def _get_url(self, item):
        return reverse('detail-view', kwargs=dict(pk=item.pk))

    def test_get_filtered_detail_view(self):
        """
        GET requests to filtered RetrieveAPIView that have a filter_class set
        should return filtered results.
        """
        item = self.objects.all()[0]
        data = self._serialize_object(item)

        # Basic test with no filter.
        response = self.client.get(self._get_url(item))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, data)

        # Tests that the decimal filter set that should fail.
        search_decimal = Decimal('4.25')
        high_item = self.objects.filter(decimal__gt=search_decimal)[0]
        response = self.client.get(
            '{url}'.format(url=self._get_url(high_item)),
            {'decimal': '{param}'.format(param=search_decimal)})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Tests that the decimal filter set that should succeed.
        search_decimal = Decimal('4.25')
        low_item = self.objects.filter(decimal__lt=search_decimal)[0]
        low_item_data = self._serialize_object(low_item)
        response = self.client.get(
            '{url}'.format(url=self._get_url(low_item)),
            {'decimal': '{param}'.format(param=search_decimal)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, low_item_data)

        # Tests that multiple filters works.
        search_decimal = Decimal('5.25')
        search_date = datetime.date(2012, 10, 2)
        valid_item = self.objects.filter(decimal__lt=search_decimal, date__gt=search_date)[0]
        valid_item_data = self._serialize_object(valid_item)
        response = self.client.get(
            '{url}'.format(url=self._get_url(valid_item)), {
                'decimal': '{decimal}'.format(decimal=search_decimal),
                'date': '{date}'.format(date=search_date)
            })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, valid_item_data)


class DjangoFilterOrderingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DjangoFilterOrderingModel
        fields = '__all__'


class DjangoFilterOrderingTests(TestCase):
    def setUp(self):
        data = [{
            'date': datetime.date(2012, 10, 8),
            'text': 'abc'
        }, {
            'date': datetime.date(2013, 10, 8),
            'text': 'bcd'
        }, {
            'date': datetime.date(2014, 10, 8),
            'text': 'cde'
        }]

        for d in data:
            DjangoFilterOrderingModel.objects.create(**d)

    def test_default_ordering(self):
        class DjangoFilterOrderingView(generics.ListAPIView):
            serializer_class = DjangoFilterOrderingSerializer
            queryset = DjangoFilterOrderingModel.objects.all()
            filter_backends = (DjangoFilterBackend,)
            filter_fields = ['text']
            ordering = ('-date',)

        view = DjangoFilterOrderingView.as_view()
        request = factory.get('/')
        response = view(request)

        self.assertEqual(
            response.data,
            [
                {'id': 3, 'date': '2014-10-08', 'text': 'cde'},
                {'id': 2, 'date': '2013-10-08', 'text': 'bcd'},
                {'id': 1, 'date': '2012-10-08', 'text': 'abc'}
            ]
        )
