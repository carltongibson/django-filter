
from django.test import TestCase

from django_filters.rest_framework import FilterSet, filters
from django_filters.widgets import BooleanWidget

from ..models import User, Article


class FilterSetFilterForFieldTests(TestCase):

    def test_isodatetimefilter(self):
        field = Article._meta.get_field('published')
        result = FilterSet.filter_for_field(field, 'published')
        self.assertIsInstance(result, filters.IsoDateTimeFilter)
        self.assertEqual(result.name, 'published')

    def test_booleanfilter_widget(self):
        field = User._meta.get_field('is_active')
        result = FilterSet.filter_for_field(field, 'is_active')
        self.assertIsInstance(result, filters.BooleanFilter)
        self.assertEqual(result.widget, BooleanWidget)
