
from django.test import TestCase

from django_filters.rest_framework import filters
from django_filters.widgets import BooleanWidget


class BooleanFilterTests(TestCase):

    def test_widget(self):
        # Ensure that `BooleanFilter` uses the correct widget when importing
        # from `rest_framework.filters`.
        f = filters.BooleanFilter()

        self.assertEqual(f.extra['widget'], BooleanWidget)
