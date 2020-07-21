import inspect

from django.test import TestCase

from django_filters.rest_framework import filters
from django_filters.widgets import BooleanWidget


class ModuleImportTests(TestCase):
    def is_filter(self, name, value):
        return (
            isinstance(value, type) and issubclass(value, filters.Filter)
        )

    def test_imports(self):
        # msg = "Expected `filters.%s` to be imported in `filters.__all__`"
        filter_classes = [
            key for key, value
            in inspect.getmembers(filters)
            if isinstance(value, type) and issubclass(value, filters.Filter)
        ]

        # sanity check
        self.assertIn('Filter', filter_classes)
        self.assertIn('BooleanFilter', filter_classes)

        for f in filter_classes:
            self.assertIn(f, filters.__all__)


class BooleanFilterTests(TestCase):

    def test_widget(self):
        # Ensure that `BooleanFilter` uses the correct widget when importing
        # from `rest_framework.filters`.
        f = filters.BooleanFilter()

        self.assertEqual(f.extra['widget'], BooleanWidget)
