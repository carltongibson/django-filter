
import warnings

from django.test import TestCase

from django_filters import FilterSet, filters


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


class FilterNameDeprecationTests(TestCase):

    def test_declaration(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                foo = filters.CharFilter(name='foo')

        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[0].category, DeprecationWarning))
        self.assertIn("`Filter.name` has been renamed to `Filter.field_name`.", str(w[0].message))

    def test_name_property(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            filters.CharFilter().name

        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[0].category, DeprecationWarning))
        self.assertIn("`Filter.name` has been renamed to `Filter.field_name`.", str(w[0].message))

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            filters.CharFilter().name = 'bar'

        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[0].category, DeprecationWarning))
        self.assertIn("`Filter.name` has been renamed to `Filter.field_name`.", str(w[0].message))
