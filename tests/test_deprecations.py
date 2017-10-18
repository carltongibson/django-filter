
import warnings

from django.test import TestCase

from django_filters import FilterSet


class TogetherOptionDeprecationTests(TestCase):

    def test_deprecation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    together = ['a', 'b']

        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[0].category, DeprecationWarning))
        self.assertIn('The `Meta.together` option has been deprecated', str(w[0].message))
