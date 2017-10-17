from unittest import skipIf

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from django_filters.compat import is_crispy
from django_filters.rest_framework import FilterSet, filters
from django_filters.widgets import BooleanWidget

from ..models import Article, User


class ArticleFilter(FilterSet):
    class Meta:
        model = Article
        fields = ['author']


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
        self.assertEqual(result.extra['widget'], BooleanWidget)


@skipIf(is_crispy(), 'django_crispy_forms must be installed')
@override_settings(INSTALLED_APPS=settings.INSTALLED_APPS + ('crispy_forms', ))
class CrispyFormsCompatTests(TestCase):

    def test_crispy_helper(self):
        # ensure the helper is present on the form
        self.assertTrue(hasattr(ArticleFilter().form, 'helper'))

    def test_form_initialization(self):
        # ensure that crispy compat does not prematurely initialize the form
        self.assertFalse(hasattr(ArticleFilter(), '_form'))
