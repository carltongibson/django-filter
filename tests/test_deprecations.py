
import warnings
from django.test import TestCase

from django_filters import FilterSet
from django_filters.filters import CharFilter
from .models import User
from .models import NetworkSetting
from .models import SubnetMaskField


class UserFilter(FilterSet):
    class Meta:
        model = User
        fields = '__all__'


class FilterSetContainerDeprecationTests(TestCase):

    def test__iter__notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            [obj for obj in UserFilter()]

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test__getitem__notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            with self.assertRaises(IndexError):
                UserFilter()[0]

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test__len__notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            len(UserFilter())

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test__count__notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            UserFilter().count()

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))


class FilterSetMetaDeprecationTests(TestCase):
    def test_fields_not_set(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = User

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("Not setting Meta.fields with Meta.model is undocumented behavior", str(w[-1].message))

    def test_fields_is_none(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = User
                    fields = None

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("Setting 'Meta.fields = None' is undocumented behavior", str(w[-1].message))

    def test_fields_not_set_ignore_unknown(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = NetworkSetting

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("Not setting Meta.fields with Meta.model is undocumented behavior", str(w[-1].message))

        self.assertNotIn('mask', F.base_filters.keys())

    def test_fields_not_set_with_override(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                filter_overrides = {
                    SubnetMaskField: {'filter_class': CharFilter}
                }

                class Meta:
                    model = NetworkSetting

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("Not setting Meta.fields with Meta.model is undocumented behavior", str(w[-1].message))

        self.assertEqual(list(F.base_filters.keys()), ['ip', 'mask'])
