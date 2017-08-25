from __future__ import unicode_literals

import datetime
import warnings
from decimal import Decimal
from unittest import skipIf

from django.db.models import BooleanField
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework import generics, serializers
from rest_framework.test import APIRequestFactory

from django_filters import compat, filters
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    backends
)

from .models import FilterableItem

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


@skipIf(compat.coreapi is None, 'coreapi must be installed')
class GetSchemaFieldsTests(TestCase):
    def test_fields_with_filter_fields_list(self):
        backend = DjangoFilterBackend()
        fields = backend.get_schema_fields(FilterFieldsRootView())
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['decimal', 'date'])

    def test_filter_fields_list_with_bad_get_queryset(self):
        """
        See:
          * https://github.com/carltongibson/django-filter/issues/551
        """
        class BadGetQuerySetView(FilterFieldsRootView):
            def get_queryset(self):
                raise AttributeError("I don't have that")

        backend = DjangoFilterBackend()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            fields = backend.get_schema_fields(BadGetQuerySetView())
            self.assertEqual(fields, [], "get_schema_fields should handle AttributeError")

            warning = "{} is not compatible with schema generation".format(BadGetQuerySetView)
            self.assertEqual(len(w), 1)
            self.assertEqual(str(w[0].message), warning)

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
        schemas = [f.schema for f in fields]
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['text', 'decimal', 'date'])
        self.assertIsInstance(schemas[0], compat.coreschema.String)
        self.assertIsInstance(schemas[1], compat.coreschema.Number)
        self.assertIsInstance(schemas[2], compat.coreschema.String)

    def test_field_required(self):
        class RequiredFieldsFilter(SeveralFieldsFilter):
            required_text = filters.CharFilter(required=True)

            class Meta(SeveralFieldsFilter.Meta):
                fields = SeveralFieldsFilter.Meta.fields + ['required_text']

        class FilterClassWithRequiredFieldsView(FilterClassRootView):
            filter_class = RequiredFieldsFilter

        backend = DjangoFilterBackend()
        fields = backend.get_schema_fields(FilterClassWithRequiredFieldsView())
        required = [f.required for f in fields]
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['text', 'decimal', 'date', 'required_text'])
        self.assertFalse(required[0])
        self.assertFalse(required[1])
        self.assertFalse(required[2])
        self.assertTrue(required[3])

    def tests_field_with_request_callable(self):
        def qs(request):
            # users expect a valid request object to be provided which cannot
            # be guaranteed during schema generation.
            self.fail("callable queryset should not be invoked during schema generation")

        class F(SeveralFieldsFilter):
            f = filters.ModelChoiceFilter(queryset=qs)

        class View(FilterClassRootView):
            filter_class = F

        view = View()
        view.request = factory.get('/')
        backend = DjangoFilterBackend()
        fields = backend.get_schema_fields(view)
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['text', 'decimal', 'date', 'f'])


class TemplateTests(TestCase):
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
            </p>
            <p>
                <label for="id_date">Date:</label>
                <input id="id_date" name="date" type="text" />
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

    def test_multiple_engines(self):
        # See: https://github.com/carltongibson/django-filter/issues/578
        DTL = {'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True}
        ALT = {'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True, 'NAME': 'alt'}

        # multiple DTL backends
        with override_settings(TEMPLATES=[DTL, ALT]):
            self.test_backend_output()


class DefaultFilterSetTests(TestCase):
    def test_default_meta_inheritance(self):
        # https://github.com/carltongibson/django-filter/issues/663

        class F(FilterSet):
            class Meta:
                filter_overrides = {BooleanField: {}}

        class Backend(DjangoFilterBackend):
            default_filter_set = F

        view = FilterFieldsRootView()
        backend = Backend()

        filter_class = backend.get_filter_class(view, view.get_queryset())
        filter_overrides = filter_class._meta.filter_overrides

        # derived filter_class.Meta should inherit from default_filter_set.Meta
        self.assertIn(BooleanField, filter_overrides)
        self.assertDictEqual(filter_overrides[BooleanField], {})
