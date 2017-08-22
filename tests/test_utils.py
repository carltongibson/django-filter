import datetime
import unittest

import django
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import ForeignObjectRel
from django.forms import ValidationError
from django.test import TestCase, override_settings
from django.utils.functional import Promise
from django.utils.timezone import get_default_timezone

from django_filters import STRICTNESS, FilterSet
from django_filters.exceptions import FieldLookupError
from django_filters.utils import (
    get_field_parts,
    get_model_field,
    handle_timezone,
    label_for_filter,
    raw_validation,
    resolve_field,
    verbose_field_name,
    verbose_lookup_expr
)

from .models import (
    Account,
    Article,
    Book,
    Business,
    Company,
    HiredWorker,
    NetworkSetting,
    User
)


class GetFieldPartsTests(TestCase):

    def test_field(self):
        parts = get_field_parts(User, 'username')

        self.assertEqual(len(parts), 1)
        self.assertIsInstance(parts[0], models.CharField)

    def test_non_existent_field(self):
        result = get_model_field(User, 'unknown__name')
        self.assertIsNone(result)

    def test_forwards_related_field(self):
        parts = get_field_parts(User, 'favorite_books__title')

        self.assertEqual(len(parts), 2)
        self.assertIsInstance(parts[0], models.ManyToManyField)
        self.assertIsInstance(parts[1], models.CharField)

    def test_reverse_related_field(self):
        parts = get_field_parts(User, 'manager_of__users__username')

        self.assertEqual(len(parts), 3)
        self.assertIsInstance(parts[0], ForeignObjectRel)
        self.assertIsInstance(parts[1], models.ManyToManyField)
        self.assertIsInstance(parts[2], models.CharField)


class GetModelFieldTests(TestCase):

    def test_non_existent_field(self):
        result = get_model_field(User, 'unknown__name')
        self.assertIsNone(result)

    def test_related_field(self):
        result = get_model_field(Business, 'hiredworker__worker')
        self.assertEqual(result, HiredWorker._meta.get_field('worker'))


class ResolveFieldTests(TestCase):

    def test_resolve_plain_lookups(self):
        """
        Check that the standard query terms can be correctly resolved.
        eg, an 'EXACT' lookup on a user's username
        """
        model_field = User._meta.get_field('username')
        lookups = model_field.class_lookups.keys()

        # This is simple - the final ouput of an untransformed field is itself.
        # The lookups are the default lookups registered to the class.
        for term in lookups:
            field, lookup = resolve_field(model_field, term)
            self.assertIsInstance(field, models.CharField)
            self.assertEqual(lookup, term)

    def test_resolve_forward_related_lookups(self):
        """
        Check that lookups can be resolved for related fields
        in the forwards direction.
        """
        lookups = ['exact', 'gte', 'gt', 'lte', 'lt', 'in', 'isnull', ]

        # ForeignKey
        model_field = Article._meta.get_field('author')
        for term in lookups:
            field, lookup = resolve_field(model_field, term)
            self.assertIsInstance(field, models.ForeignKey)
            self.assertEqual(lookup, term)

        # ManyToManyField
        model_field = User._meta.get_field('favorite_books')
        for term in lookups:
            field, lookup = resolve_field(model_field, term)
            self.assertIsInstance(field, models.ManyToManyField)
            self.assertEqual(lookup, term)

    @unittest.skipIf(django.VERSION < (1, 9), "version does not reverse lookups")
    def test_resolve_reverse_related_lookups(self):
        """
        Check that lookups can be resolved for related fields
        in the reverse direction.
        """
        lookups = ['exact', 'gte', 'gt', 'lte', 'lt', 'in', 'isnull', ]

        # ManyToOneRel
        model_field = User._meta.get_field('article')
        for term in lookups:
            field, lookup = resolve_field(model_field, term)
            self.assertIsInstance(field, models.ManyToOneRel)
            self.assertEqual(lookup, term)

        # ManyToManyRel
        model_field = Book._meta.get_field('lovers')
        for term in lookups:
            field, lookup = resolve_field(model_field, term)
            self.assertIsInstance(field, models.ManyToManyRel)
            self.assertEqual(lookup, term)

    @unittest.skipIf(django.VERSION < (1, 9), "version does not support transformed lookup expressions")
    def test_resolve_transformed_lookups(self):
        """
        Check that chained field transforms are correctly resolved.
        eg, a 'date__year__gte' lookup on an article's 'published' timestamp.
        """
        # Use a DateTimeField, so we can check multiple transforms.
        # eg, date__year__gte
        model_field = Article._meta.get_field('published')

        standard_lookups = [
            'exact',
            'iexact',
            'gte',
            'gt',
            'lte',
            'lt',
        ]

        date_lookups = [
            'year',
            'month',
            'day',
            'week_day',
        ]

        datetime_lookups = date_lookups + [
            'hour',
            'minute',
            'second',
        ]

        # ex: 'date__gt'
        for lookup in standard_lookups:
            field, resolved_lookup = resolve_field(model_field, LOOKUP_SEP.join(['date', lookup]))
            self.assertIsInstance(field, models.DateField)
            self.assertEqual(resolved_lookup, lookup)

        # ex: 'year__iexact'
        for part in datetime_lookups:
            for lookup in standard_lookups:
                field, resolved_lookup = resolve_field(model_field, LOOKUP_SEP.join([part, lookup]))
                self.assertIsInstance(field, models.IntegerField)
                self.assertEqual(resolved_lookup, lookup)

        # ex: 'date__year__lte'
        for part in date_lookups:
            for lookup in standard_lookups:
                field, resolved_lookup = resolve_field(model_field, LOOKUP_SEP.join(['date', part, lookup]))
                self.assertIsInstance(field, models.IntegerField)
                self.assertEqual(resolved_lookup, lookup)

    @unittest.skipIf(django.VERSION < (1, 9), "version does not support transformed lookup expressions")
    def test_resolve_implicit_exact_lookup(self):
        # Use a DateTimeField, so we can check multiple transforms.
        # eg, date__year__gte
        model_field = Article._meta.get_field('published')

        field, lookup = resolve_field(model_field, 'date')
        self.assertIsInstance(field, models.DateField)
        self.assertEqual(lookup, 'exact')

        field, lookup = resolve_field(model_field, 'date__year')
        self.assertIsInstance(field, models.IntegerField)
        self.assertEqual(lookup, 'exact')

    def test_invalid_lookup_expression(self):
        model_field = Article._meta.get_field('published')

        with self.assertRaises(FieldLookupError) as context:
            resolve_field(model_field, 'invalid_lookup')

        exc = str(context.exception)
        self.assertIn(str(model_field), exc)
        self.assertIn('invalid_lookup', exc)

    def test_invalid_transformed_lookup_expression(self):
        model_field = Article._meta.get_field('published')

        with self.assertRaises(FieldLookupError) as context:
            resolve_field(model_field, 'date__invalid_lookup')

        exc = str(context.exception)
        self.assertIn(str(model_field), exc)
        self.assertIn('date__invalid_lookup', exc)


class VerboseFieldNameTests(TestCase):

    def test_none(self):
        verbose_name = verbose_field_name(Article, None)
        self.assertEqual(verbose_name, '[invalid name]')

    def test_invalid_name(self):
        verbose_name = verbose_field_name(Article, 'foobar')
        self.assertEqual(verbose_name, '[invalid name]')

    def test_field(self):
        verbose_name = verbose_field_name(Article, 'author')
        self.assertEqual(verbose_name, 'author')

    def test_field_with_verbose_name(self):
        verbose_name = verbose_field_name(Article, 'name')
        self.assertEqual(verbose_name, 'title')

    def test_field_all_caps(self):
        verbose_name = verbose_field_name(NetworkSetting, 'cidr')
        self.assertEqual(verbose_name, 'CIDR')

    def test_forwards_related_field(self):
        verbose_name = verbose_field_name(Article, 'author__username')
        self.assertEqual(verbose_name, 'author username')

    def test_backwards_related_field(self):
        verbose_name = verbose_field_name(Book, 'lovers__first_name')
        self.assertEqual(verbose_name, 'lovers first name')

    def test_backwards_related_field_multi_word(self):
        verbose_name = verbose_field_name(User, 'manager_of')
        self.assertEqual(verbose_name, 'manager of')

    def test_lazy_text(self):
        # sanity check
        field = User._meta.get_field('username')
        self.assertIsInstance(field.verbose_name, Promise)

        verbose_name = verbose_field_name(User, 'username')
        self.assertEqual(verbose_name, 'username')

    def test_forwards_fk(self):
        verbose_name = verbose_field_name(Article, 'author')
        self.assertEqual(verbose_name, 'author')

    def test_backwards_fk(self):
        # https://github.com/carltongibson/django-filter/issues/716

        # related_name is set
        verbose_name = verbose_field_name(Company, 'locations')
        self.assertEqual(verbose_name, 'locations')

        # related_name not set. Auto-generated relation is `article_set`
        # _meta.get_field raises FieldDoesNotExist
        verbose_name = verbose_field_name(User, 'article_set')
        self.assertEqual(verbose_name, '[invalid name]')

        # WRONG NAME! Returns ManyToOneRel with related_name == None.
        verbose_name = verbose_field_name(User, 'article')
        self.assertEqual(verbose_name, '[invalid name]')


class VerboseLookupExprTests(TestCase):

    def test_exact(self):
        # Exact should default to empty. A verbose expression is unnecessary,
        # and this behavior works well with list syntax for `Meta.fields`.
        verbose_lookup = verbose_lookup_expr('exact')
        self.assertEqual(verbose_lookup, '')

    def test_verbose_expression(self):
        verbose_lookup = verbose_lookup_expr('date__lt')
        self.assertEqual(verbose_lookup, 'date is less than')

    def test_missing_keys(self):
        verbose_lookup = verbose_lookup_expr('foo__bar__lt')
        self.assertEqual(verbose_lookup, 'foo bar is less than')

    @override_settings(FILTERS_VERBOSE_LOOKUPS={'exact': 'is equal to'})
    def test_overridden_settings(self):
        verbose_lookup = verbose_lookup_expr('exact')
        self.assertEqual(verbose_lookup, 'is equal to')


class LabelForFilterTests(TestCase):

    def test_standard_label(self):
        label = label_for_filter(Article, 'name', 'in')
        self.assertEqual(label, 'Title is in')

    def test_related_model(self):
        label = label_for_filter(Article, 'author__first_name', 'in')
        self.assertEqual(label, 'Author first name is in')

    def test_exclusion_label(self):
        label = label_for_filter(Article, 'name', 'in', exclude=True)
        self.assertEqual(label, 'Exclude title is in')

    def test_related_model_exclusion(self):
        label = label_for_filter(Article, 'author__first_name', 'in', exclude=True)
        self.assertEqual(label, 'Exclude author first name is in')

    def test_exact_lookup(self):
        label = label_for_filter(Article, 'name', 'exact')
        self.assertEqual(label, 'Title')

    def test_field_all_caps(self):
        label = label_for_filter(NetworkSetting, 'cidr', 'contains', exclude=True)
        self.assertEqual(label, 'Exclude CIDR contains')


class HandleTimezone(TestCase):

    @unittest.skipIf(django.VERSION < (1, 9), 'version doesnt supports is_dst parameter for make_aware')
    @override_settings(TIME_ZONE='America/Sao_Paulo')
    def test_handle_dst_ending(self):
        dst_ending_date = datetime.datetime(2017, 2, 18, 23, 59, 59, 999999)
        handled = handle_timezone(dst_ending_date, False)
        self.assertEqual(handled, get_default_timezone().localize(dst_ending_date, False))

    @unittest.skipIf(django.VERSION < (1, 9), 'version doesnt supports is_dst parameter for make_aware')
    @override_settings(TIME_ZONE='America/Sao_Paulo')
    def test_handle_dst_starting(self):
        dst_starting_date = datetime.datetime(2017, 10, 15, 0, 0, 0, 0)
        handled = handle_timezone(dst_starting_date, True)
        self.assertEqual(handled, get_default_timezone().localize(dst_starting_date, True))


class RawValidationDataTests(TestCase):
    def test_simple(self):
        class F(FilterSet):
            class Meta:
                model = Article
                fields = ['id', 'author', 'name']
                strict = STRICTNESS.RAISE_VALIDATION_ERROR

        f = F(data={'id': 'foo', 'author': 'bar', 'name': 'baz'})
        with self.assertRaises(ValidationError) as exc:
            f.qs

        self.assertDictEqual(raw_validation(exc.exception), {
            'id': ['Enter a number.'],
            'author': ['Select a valid choice. That choice is not one of the available choices.'],
        })
