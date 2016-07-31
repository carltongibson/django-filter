
import warnings
from django.test import TestCase

from django_filters import FilterSet
from .models import User


class UserFilter(FilterSet):
    class Meta:
        model = User


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
