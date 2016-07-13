
import unittest

import django
from django.test import TestCase
from django.db import models
from django.db.models.constants import LOOKUP_SEP

from django_filters.utils import get_model_field, resolve_field
from django_filters.exceptions import FieldLookupError

from .models import User
from .models import Article
from .models import Book
from .models import HiredWorker
from .models import Business


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
