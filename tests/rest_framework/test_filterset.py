from unittest import skipIf

from django import forms
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from django_filters import NumberFilter
from django_filters.compat import is_crispy
from django_filters.rest_framework import FilterSet, filters
from django_filters.widgets import BooleanWidget

from ..models import Article, BankAccount, User


class ArticleFilter(FilterSet):
    class Meta:
        model = Article
        fields = ['author']


class FilterSetFilterForFieldTests(TestCase):

    def test_isodatetimefilter(self):
        field = Article._meta.get_field('published')
        result = FilterSet.filter_for_field(field, 'published')
        self.assertIsInstance(result, filters.IsoDateTimeFilter)
        self.assertEqual(result.field_name, 'published')

    def test_booleanfilter_widget(self):
        field = User._meta.get_field('is_active')
        result = FilterSet.filter_for_field(field, 'is_active')
        self.assertIsInstance(result, filters.BooleanFilter)
        self.assertEqual(result.extra['widget'], BooleanWidget)

    def test_booleanfilter_widget_nullbooleanfield(self):
        field = User._meta.get_field('is_employed')
        result = FilterSet.filter_for_field(field, 'is_employed')
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


class ExtraFieldForm(forms.Form):
    extra_field = forms.BooleanField(required=False)

    def clean(self):
        extra_field = self.cleaned_data.get('extra_field')
        if extra_field:
            self.cleaned_data['number'] = 2
        return self.cleaned_data


class ExtraFieldFilterSet(FilterSet):
    number = NumberFilter(field_name='amount_saved')

    class Meta:
        model = BankAccount
        fields = ['number']
        form = ExtraFieldForm


class ExtraFieldInFormTests(TestCase):

    def test_filter_queyset_with_extra_form_fields(self):
        queryset = BankAccount.objects.all()
        e = ExtraFieldFilterSet({'number': 1, 'extra_field': True}, queryset=queryset)
        e.is_valid()
        e.filter_queryset(queryset=queryset)
