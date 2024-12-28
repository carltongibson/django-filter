from unittest import mock

from django.db.models import BooleanField
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework import generics, serializers
from rest_framework.test import APIRequestFactory

from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, backends

from ..models import Article
from .models import CategoryItem, FilterableItem

factory = APIRequestFactory()


class FilterableItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterableItem
        fields = "__all__"


class CategoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryItem
        fields = "__all__"


# These class are used to test a filter class.
class SeveralFieldsFilter(FilterSet):
    text = filters.CharFilter(lookup_expr="icontains")
    decimal = filters.NumberFilter(lookup_expr="lt")
    date = filters.DateFilter(lookup_expr="gt")

    class Meta:
        model = FilterableItem
        fields = ["text", "decimal", "date"]


# Basic filter on a list view.
class FilterableItemView(generics.ListCreateAPIView):
    queryset = FilterableItem.objects.all()
    serializer_class = FilterableItemSerializer
    filter_backends = (DjangoFilterBackend,)


class FilterFieldsRootView(FilterableItemView):
    filterset_fields = ["decimal", "date"]


class FilterClassRootView(FilterableItemView):
    filterset_class = SeveralFieldsFilter


class CategoryItemView(generics.ListCreateAPIView):
    queryset = CategoryItem.objects.all()
    serializer_class = CategoryItemSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ["category"]


class GetFilterClassTests(TestCase):
    def test_filterset_class(self):
        class Filter(FilterSet):
            class Meta:
                model = FilterableItem
                fields = "__all__"

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
                fields = "__all__"

        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_class = Filter

        filterset_class = backend.get_filterset_class(view, None)
        self.assertIs(filterset_class, Filter)

    def test_filterset_fields(self):
        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_fields = ["text", "decimal", "date"]
        queryset = FilterableItem.objects.all()

        filterset_class = backend.get_filterset_class(view, queryset)
        self.assertEqual(filterset_class._meta.fields, view.filterset_fields)

    def test_filterset_fields_malformed(self):
        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_fields = ["non_existent"]
        queryset = FilterableItem.objects.all()

        msg = "'Meta.fields' must not contain non-model field names: non_existent"
        with self.assertRaisesMessage(TypeError, msg):
            backend.get_filterset_class(view, queryset)

    def test_filterset_fields_no_queryset(self):
        backend = DjangoFilterBackend()
        view = FilterableItemView()
        view.filterset_fields = ["text", "decimal", "date"]

        filterset_class = backend.get_filterset_class(view, None)
        self.assertIsNone(filterset_class)


class TemplateTests(TestCase):
    def test_backend_output(self):
        """
        Ensure backend renders default if template path does not exist
        """
        view = FilterFieldsRootView()
        backend = view.filter_backends[0]
        request = view.initialize_request(factory.get("/"))
        html = backend().to_html(request, view.get_queryset(), view)

        self.assertHTMLEqual(
            html,
            """
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
        """,
        )

    def test_template_path(self):
        view = FilterFieldsRootView()

        class Backend(view.filter_backends[0]):
            template = "filter_template.html"

        request = view.initialize_request(factory.get("/"))
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
        DTL = {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
        }
        ALT = {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
            "NAME": "alt",
        }

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
                fields = ["id", "author", "name"]

        view = FilterFieldsRootView()
        backend = DjangoFilterBackend()
        request = factory.get("/?id=foo&author=bar&name=baz")
        request = view.initialize_request(request)
        queryset = Article.objects.all()
        view.filterset_class = F

        with self.assertRaises(serializers.ValidationError) as exc:
            backend.filter_queryset(request, queryset, view)

        # test output, does not include error code
        self.assertDictEqual(
            exc.exception.detail,
            {
                "id": ["Enter a number."],
                "author": [
                    "Select a valid choice. "
                    "That choice is not one of the available choices."
                ],
            },
        )


class DjangoFilterBackendTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.backend = DjangoFilterBackend()
        cls.backend.get_filterset_class = lambda x, y: None

    def test_get_filterset_none_filter_class(self):
        filterset = self.backend.get_filterset(mock.Mock(), mock.Mock(), mock.Mock())
        self.assertIsNone(filterset)

    def test_filter_queryset_none_filter_class(self):
        prev_qs = mock.Mock()
        qs = self.backend.filter_queryset(mock.Mock(), prev_qs, mock.Mock())
        self.assertIs(qs, prev_qs)

    def test_to_html_none_filter_class(self):
        html = self.backend.to_html(mock.Mock(), mock.Mock(), mock.Mock())
        self.assertIsNone(html)

    @mock.patch("django_filters.compat.is_crispy", return_value=True)
    def test_template_crispy(self, _):
        self.assertEqual(
            self.backend.template, "django_filters/rest_framework/crispy_form.html"
        )
