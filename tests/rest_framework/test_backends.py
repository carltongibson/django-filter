import warnings
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

from ..models import Article
from .models import FilterableItem

factory = APIRequestFactory()


class FilterableItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterableItem
        fields = '__all__'


# These class are used to test a filter class.
class SeveralFieldsFilter(FilterSet):
    text = filters.CharFilter(lookup_expr='icontains')
    decimal = filters.NumberFilter(lookup_expr='lt')
    date = filters.DateFilter(lookup_expr='gt')

    class Meta:
        model = FilterableItem
        fields = ['text', 'decimal', 'date']


# Basic filter on a list view.
class FilterableItemView(generics.ListCreateAPIView):
    queryset = FilterableItem.objects.all()
    serializer_class = FilterableItemSerializer
    filter_backends = (DjangoFilterBackend,)


class FilterFieldsRootView(FilterableItemView):
    filterset_fields = ['decimal', 'date']


class FilterClassRootView(FilterableItemView):
    filterset_class = SeveralFieldsFilter


class GetFilterClassTests(TestCase):

    def test_filterset_class(self):
        class Filter(FilterSet):
            class Meta:
                model = FilterableItem
                fields = '__all__'

        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_class = Filter
        queryset = FilterableItem.objects.all()

        filterset_class = backend.get_filterset_class(view, queryset)
        self.assertIs(filterset_class, Filter)

    def test_filterset_class_no_meta(self):
        class Filter(FilterSet):
            pass

        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_class = Filter
        queryset = FilterableItem.objects.all()

        filterset_class = backend.get_filterset_class(view, queryset)
        self.assertIs(filterset_class, Filter)

    def test_filterset_class_no_queryset(self):
        class Filter(FilterSet):
            class Meta:
                model = FilterableItem
                fields = '__all__'

        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_class = Filter

        filterset_class = backend.get_filterset_class(view, None)
        self.assertIs(filterset_class, Filter)

    def test_filterset_fields(self):
        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_fields = ['text', 'decimal', 'date']
        queryset = FilterableItem.objects.all()

        filterset_class = backend.get_filterset_class(view, queryset)
        self.assertEqual(filterset_class._meta.fields, view.filterset_fields)

    def test_filterset_fields_malformed(self):
        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_fields = ['non_existent']
        queryset = FilterableItem.objects.all()

        msg = "'Meta.fields' contains fields that are not defined on this FilterSet: non_existent"
        with self.assertRaisesMessage(TypeError, msg):
            backend.get_filterset_class(view, queryset)

    def test_filterset_fields_no_queryset(self):
        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_fields = ['text', 'decimal', 'date']

        filterset_class = backend.get_filterset_class(view, None)
        self.assertIsNone(filterset_class)


@skipIf(compat.coreapi is None, 'coreapi must be installed')
class GetSchemaFieldsTests(TestCase):
    def test_fields_with_filterset_fields_list(self):
        backend = DjangoFilterBackend()
        fields = backend.get_schema_fields(FilterFieldsRootView())
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['decimal', 'date'])

    def test_filterset_fields_list_with_bad_get_queryset(self):
        """
        See:
          * https://github.com/carltongibson/django-filter/issues/551
        """
        class BadGetQuerySetView(FilterFieldsRootView):
            filterset_fields = ['decimal', 'date']

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

    def test_malformed_filterset_fields(self):
        # Malformed filter fields should raise an exception
        class View(FilterFieldsRootView):
            filterset_fields = ['non_existent']

        backend = DjangoFilterBackend()

        msg = "'Meta.fields' contains fields that are not defined on this FilterSet: non_existent"
        with self.assertRaisesMessage(TypeError, msg):
            backend.get_schema_fields(View())

    def test_fields_with_filterset_fields_dict(self):
        class DictFilterFieldsRootView(FilterFieldsRootView):
            filterset_fields = {
                'decimal': ['exact', 'lt', 'gt'],
            }

        backend = DjangoFilterBackend()
        fields = backend.get_schema_fields(DictFilterFieldsRootView())
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['decimal', 'decimal__lt', 'decimal__gt'])

    def test_fields_with_filterset_class(self):
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
            filterset_class = RequiredFieldsFilter

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
            filterset_class = F

        view = View()
        view.request = factory.get('/')
        backend = DjangoFilterBackend()
        fields = backend.get_schema_fields(view)
        fields = [f.name for f in fields]

        self.assertEqual(fields, ['text', 'decimal', 'date', 'f'])


class GetSchemaOperationParametersTests(TestCase):
    def test_get_operation_parameters_with_filterset_fields_list(self):
        backend = DjangoFilterBackend()
        fields = backend.get_schema_operation_parameters(FilterFieldsRootView())
        fields = [f['name'] for f in fields]

        self.assertEqual(fields, ['decimal', 'date'])


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


class AutoFilterSetTests(TestCase):
    def test_autofilter_meta_inheritance(self):
        # https://github.com/carltongibson/django-filter/issues/663

        class F(FilterSet):
            class Meta:
                filter_overrides = {BooleanField: {}}

        class Backend(DjangoFilterBackend):
            filterset_base = F

        view = FilterFieldsRootView()
        backend = Backend()

        filterset_class = backend.get_filterset_class(view, view.get_queryset())
        filter_overrides = filterset_class._meta.filter_overrides

        # derived filterset_class.Meta should inherit from default_filter_set.Meta
        self.assertIn(BooleanField, filter_overrides)
        self.assertDictEqual(filter_overrides[BooleanField], {})


class ValidationErrorTests(TestCase):

    def test_errors(self):
        class F(FilterSet):
            class Meta:
                model = Article
                fields = ['id', 'author', 'name']

        view = FilterFieldsRootView()
        backend = DjangoFilterBackend()
        request = factory.get('/?id=foo&author=bar&name=baz')
        request = view.initialize_request(request)
        queryset = Article.objects.all()
        view.filterset_class = F

        with self.assertRaises(serializers.ValidationError) as exc:
            backend.filter_queryset(request, queryset, view)

        # test output, does not include error code
        self.assertDictEqual(exc.exception.detail, {
            'id': ['Enter a number.'],
            'author': ['Select a valid choice. That choice is not one of the available choices.'],
        })


class RenamedBackendAttributesTests(TestCase):
    def test_get_filter_class(self):
        expected = "`Backend.get_filter_class` method should be renamed `get_filterset_class`. " \
                   "See: https://django-filter.readthedocs.io/en/master/guide/migration.html"
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter('always')

            class Backend(DjangoFilterBackend):
                def get_filter_class(self):
                    pass

        message = str(recorded.pop().message)
        self.assertEqual(message, expected)
        self.assertEqual(len(recorded), 0)

    def test_default_filter_set(self):
        expected = "`Backend.default_filter_set` attribute should be renamed `filterset_base`. " \
                   "See: https://django-filter.readthedocs.io/en/master/guide/migration.html"
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter('always')

            class Backend(DjangoFilterBackend):
                default_filter_set = None

        message = str(recorded.pop().message)
        self.assertEqual(message, expected)
        self.assertEqual(len(recorded), 0)


class RenamedViewSetAttributesTests(TestCase):

    def test_filter_class(self):
        expected = "`View.filter_class` attribute should be renamed `filterset_class`. " \
                   "See: https://django-filter.readthedocs.io/en/master/guide/migration.html"
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter('always')

            class View(generics.ListCreateAPIView):
                filter_class = None

            view = View()
            backend = DjangoFilterBackend()
            backend.get_filterset_class(view, None)

        message = str(recorded.pop().message)
        self.assertEqual(message, expected)
        self.assertEqual(len(recorded), 0)

    def test_filter_fields(self):
        expected = "`View.filter_fields` attribute should be renamed `filterset_fields`. " \
                   "See: https://django-filter.readthedocs.io/en/master/guide/migration.html"
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter('always')

            class View(generics.ListCreateAPIView):
                filter_fields = None

            view = View()
            backend = DjangoFilterBackend()
            # import pdb; pdb.set_trace()
            backend.get_filterset_class(view, None)

        message = str(recorded.pop().message)
        self.assertEqual(message, expected)
        self.assertEqual(len(recorded), 0)
