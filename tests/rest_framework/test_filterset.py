
from django.test import TestCase

from django_filters.rest_framework import FilterSet
from django_filters.filters import BooleanFilter, IsoDateTimeFilter
from django_filters.widgets import BooleanWidget

from ..models import User, Article


class FilterSetFilterForFieldTests(TestCase):

    def test_isodatetimefilter(self):
        field = Article._meta.get_field('published')
        result = FilterSet.filter_for_field(field, 'published')
        self.assertIsInstance(result, IsoDateTimeFilter)
        self.assertEqual(result.name, 'published')

    def test_booleanfilter_widget(self):
        field = User._meta.get_field('is_active')
        result = FilterSet.filter_for_field(field, 'is_active')
        self.assertIsInstance(result, BooleanFilter)
        self.assertEqual(result.widget, BooleanWidget)
