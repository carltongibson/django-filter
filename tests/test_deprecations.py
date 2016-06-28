
import warnings
from django.test import TestCase

from django_filters import FilterSet


class StrictnessDeprecationTests(TestCase):
    def test_notification(self):

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                strict = False

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_passthrough(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            class F(FilterSet):
                strict = False

            self.assertEqual(F._meta.strict, False)


class OrderByFieldDeprecationTests(TestCase):
    def test_notification(self):

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                order_by_field = 'field'

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_passthrough(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            class F(FilterSet):
                order_by_field = 'field'

            self.assertEqual(F._meta.ordering_param, 'field')
