from __future__ import absolute_import, unicode_literals

import mock
import unittest

import django
from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase

from django_filters.filterset import FilterSet
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS
from django_filters.filterset import STRICTNESS
from django_filters.filters import BooleanFilter
from django_filters.filters import CharFilter
from django_filters.filters import NumberFilter
from django_filters.filters import ChoiceFilter
from django_filters.filters import ModelChoiceFilter
from django_filters.filters import ModelMultipleChoiceFilter
from django_filters.filters import UUIDFilter
from django_filters.filters import BaseInFilter
from django_filters.filters import BaseRangeFilter

from django_filters.widgets import BooleanWidget

from .models import User
from .models import AdminUser
from .models import Article
from .models import Book
from .models import Profile
from .models import Comment
from .models import Restaurant
from .models import NetworkSetting
from .models import SubnetMaskField
from .models import Account
from .models import BankAccount
from .models import Node
from .models import DirectedNode
from .models import Worker
from .models import HiredWorker
from .models import Business
from .models import UUIDTestModel


def checkItemsEqual(L1, L2):
    """
    TestCase.assertItemsEqual() is not available in Python 2.6.
    """
    return len(L1) == len(L2) and sorted(L1) == sorted(L2)


class HelperMethodsTests(TestCase):

    @unittest.skip('todo')
    def test_get_declared_filters(self):
        pass

    @unittest.skip('todo')
    def test_filters_for_model(self):
        pass

    @unittest.skip('todo')
    def test_filterset_factory(self):
        pass


class DbFieldDefaultFiltersTests(TestCase):

    def test_expected_db_fields_get_filters(self):
        to_check = [
            models.BooleanField,
            models.CharField,
            models.CommaSeparatedIntegerField,
            models.DateField,
            models.DateTimeField,
            models.DecimalField,
            models.EmailField,
            models.FilePathField,
            models.FloatField,
            models.IntegerField,
            models.GenericIPAddressField,
            models.NullBooleanField,
            models.PositiveIntegerField,
            models.PositiveSmallIntegerField,
            models.SlugField,
            models.SmallIntegerField,
            models.TextField,
            models.TimeField,
            models.DurationField,
            models.URLField,
            models.ForeignKey,
            models.OneToOneField,
            models.ManyToManyField,
            models.UUIDField,
        ]
        msg = "%s expected to be found in FILTER_FOR_DBFIELD_DEFAULTS"

        for m in to_check:
            self.assertIn(m, FILTER_FOR_DBFIELD_DEFAULTS, msg % m.__name__)

    def test_expected_db_fields_do_not_get_filters(self):
        to_check = [
            models.Field,
            models.BigIntegerField,
            models.FileField,
            models.ImageField,
        ]
        msg = "%s expected to not be found in FILTER_FOR_DBFIELD_DEFAULTS"

        for m in to_check:
            self.assertNotIn(m, FILTER_FOR_DBFIELD_DEFAULTS, msg % m.__name__)


class FilterSetFilterForFieldTests(TestCase):

    def test_filter_found_for_field(self):
        f = User._meta.get_field('username')
        result = FilterSet.filter_for_field(f, 'username')
        self.assertIsInstance(result, CharFilter)
        self.assertEqual(result.name, 'username')

    def test_filter_found_for_uuidfield(self):
        f = UUIDTestModel._meta.get_field('uuid')
        result = FilterSet.filter_for_field(f, 'uuid')
        self.assertIsInstance(result, UUIDFilter)
        self.assertEqual(result.name, 'uuid')

    def test_filter_found_for_autofield(self):
        f = User._meta.get_field('id')
        result = FilterSet.filter_for_field(f, 'id')
        self.assertIsInstance(result, NumberFilter)
        self.assertEqual(result.name, 'id')

    def test_field_with_extras(self):
        f = User._meta.get_field('favorite_books')
        result = FilterSet.filter_for_field(f, 'favorite_books')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'favorite_books')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Book)

    def test_field_with_choices(self):
        f = User._meta.get_field('status')
        result = FilterSet.filter_for_field(f, 'status')
        self.assertIsInstance(result, ChoiceFilter)
        self.assertEqual(result.name, 'status')
        self.assertTrue('choices' in result.extra)
        self.assertIsNotNone(result.extra['choices'])

    def test_field_that_is_subclassed(self):
        f = User._meta.get_field('first_name')
        result = FilterSet.filter_for_field(f, 'first_name')
        self.assertIsInstance(result, CharFilter)

    def test_symmetrical_selfref_m2m_field(self):
        f = Node._meta.get_field('adjacents')
        result = FilterSet.filter_for_field(f, 'adjacents')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'adjacents')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Node)

    def test_non_symmetrical_selfref_m2m_field(self):
        f = DirectedNode._meta.get_field('outbound_nodes')
        result = FilterSet.filter_for_field(f, 'outbound_nodes')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'outbound_nodes')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, DirectedNode)

    def test_m2m_field_with_through_model(self):
        f = Business._meta.get_field('employees')
        result = FilterSet.filter_for_field(f, 'employees')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'employees')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Worker)

    @unittest.skipIf(django.VERSION < (1, 9), "version does not support transformed lookup expressions")
    def test_transformed_lookup_expr(self):
        f = Comment._meta.get_field('date')
        result = FilterSet.filter_for_field(f, 'date', 'year__gte')
        self.assertIsInstance(result, NumberFilter)
        self.assertEqual(result.name, 'date')

    @unittest.skip('todo')
    def test_filter_overrides(self):
        pass


class FilterSetFilterForLookupTests(TestCase):

    def test_filter_for_ISNULL_lookup(self):
        f = Article._meta.get_field('author')
        result, params = FilterSet.filter_for_lookup(f, 'isnull')
        self.assertEqual(result, BooleanFilter)
        self.assertDictEqual(params, {})

    def test_filter_for_IN_lookup(self):
        f = Article._meta.get_field('author')
        result, params = FilterSet.filter_for_lookup(f, 'in')
        self.assertTrue(issubclass(result, ModelChoiceFilter))
        self.assertTrue(issubclass(result, BaseInFilter))
        self.assertEqual(params['to_field_name'], 'id')

    def test_filter_for_RANGE_lookup(self):
        f = Article._meta.get_field('author')
        result, params = FilterSet.filter_for_lookup(f, 'range')
        self.assertTrue(issubclass(result, ModelChoiceFilter))
        self.assertTrue(issubclass(result, BaseRangeFilter))
        self.assertEqual(params['to_field_name'], 'id')

    def test_isnull_with_filter_overrides(self):
        class OFilterSet(FilterSet):
            filter_overrides = {
                models.BooleanField: {
                    'filter_class': BooleanFilter,
                    'extra': lambda f: {
                        'widget': BooleanWidget,
                    },
                },
            }

        f = Article._meta.get_field('author')
        result, params = OFilterSet.filter_for_lookup(f, 'isnull')
        self.assertEqual(result, BooleanFilter)
        self.assertEqual(params['widget'], BooleanWidget)


class FilterSetFilterForReverseFieldTests(TestCase):

    def test_reverse_o2o_relationship(self):
        f = Account._meta.get_field('profile')
        result = FilterSet.filter_for_reverse_field(f, 'profile')
        self.assertIsInstance(result, ModelChoiceFilter)
        self.assertEqual(result.name, 'profile')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Profile)

    def test_reverse_fk_relationship(self):
        f = User._meta.get_field('comments')
        result = FilterSet.filter_for_reverse_field(f, 'comments')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'comments')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Comment)

    def test_reverse_m2m_relationship(self):
        f = Book._meta.get_field('lovers')
        result = FilterSet.filter_for_reverse_field(f, 'lovers')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'lovers')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, User)

    def test_reverse_non_symmetrical_selfref_m2m_field(self):
        f = DirectedNode._meta.get_field('inbound_nodes')
        result = FilterSet.filter_for_reverse_field(f, 'inbound_nodes')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'inbound_nodes')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, DirectedNode)

    def test_reverse_m2m_field_with_through_model(self):
        f = Worker._meta.get_field('employers')
        result = FilterSet.filter_for_reverse_field(f, 'employers')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'employers')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Business)


class FilterSetClassCreationTests(TestCase):

    def test_no_filters(self):
        class F(FilterSet):
            pass

        self.assertEqual(len(F.declared_filters), 0)
        self.assertEqual(len(F.base_filters), 0)

    def test_declaring_filter(self):
        class F(FilterSet):
            username = CharFilter()

        self.assertEqual(len(F.declared_filters), 1)
        self.assertListEqual(list(F.declared_filters), ['username'])
        self.assertEqual(len(F.base_filters), 1)
        self.assertListEqual(list(F.base_filters), ['username'])

    def test_model_derived(self):
        class F(FilterSet):
            class Meta:
                model = Book

        self.assertEqual(len(F.declared_filters), 0)
        self.assertEqual(len(F.base_filters), 3)
        self.assertListEqual(list(F.base_filters),
                             ['title', 'price', 'average_rating'])

    def test_declared_and_model_derived(self):
        class F(FilterSet):
            username = CharFilter()

            class Meta:
                model = Book

        self.assertEqual(len(F.declared_filters), 1)
        self.assertEqual(len(F.base_filters), 4)
        self.assertListEqual(list(F.base_filters),
                             ['title', 'price', 'average_rating', 'username'])

    def test_meta_fields_with_declared_and_model_derived(self):
        class F(FilterSet):
            username = CharFilter()

            class Meta:
                model = Book
                fields = ('username', 'price')

        self.assertEqual(len(F.declared_filters), 1)
        self.assertEqual(len(F.base_filters), 2)
        self.assertListEqual(list(F.base_filters), ['username', 'price'])

    def test_meta_fields_dictionary_derived(self):
        class F(FilterSet):

            class Meta:
                model = Book
                fields = {'price': ['exact', 'gte', 'lte'], }

        self.assertEqual(len(F.declared_filters), 0)
        self.assertEqual(len(F.base_filters), 3)

        expected_list = ['price', 'price__gte', 'price__lte', ]
        self.assertTrue(checkItemsEqual(list(F.base_filters), expected_list))

    def test_meta_fields_containing_autofield(self):
        class F(FilterSet):
            username = CharFilter()

            class Meta:
                model = Book
                fields = ('id', 'username', 'price')

        self.assertEqual(len(F.declared_filters), 1)
        self.assertEqual(len(F.base_filters), 3)
        self.assertListEqual(list(F.base_filters), ['id', 'username', 'price'])

    def test_meta_fields_dictionary_autofield(self):
        class F(FilterSet):
            username = CharFilter()

            class Meta:
                model = Book
                fields = {'id': ['exact'],
                          'username': ['exact'],
                          }

        self.assertEqual(len(F.declared_filters), 1)
        self.assertEqual(len(F.base_filters), 2)

        expected_list = ['id', 'username']
        self.assertTrue(checkItemsEqual(list(F.base_filters), expected_list))

    def test_meta_fields_containing_unknown(self):
        with self.assertRaises(TypeError) as excinfo:
            class F(FilterSet):
                username = CharFilter()

                class Meta:
                    model = Book
                    fields = ('username', 'price', 'other')
        self.assertEqual(excinfo.exception.args, (
            "Meta.fields contains a field that isn't defined on this FilterSet: other",))

    def test_meta_fields_dictionary_containing_unknown(self):
        with self.assertRaises(TypeError):
            class F(FilterSet):

                class Meta:
                    model = Book
                    fields = {'id': ['exact'],
                              'title': ['exact'],
                              'other': ['exact'],
                             }

    def test_meta_exlude_with_declared_and_declared_wins(self):
        class F(FilterSet):
            username = CharFilter()

            class Meta:
                model = Book
                exclude = ('username', 'price')

        self.assertEqual(len(F.declared_filters), 1)
        self.assertEqual(len(F.base_filters), 3)
        self.assertListEqual(list(F.base_filters),
                             ['title', 'average_rating', 'username'])

    def test_meta_fields_and_exlude_and_exclude_wins(self):
        class F(FilterSet):
            username = CharFilter()

            class Meta:
                model = Book
                fields = ('username', 'title', 'price')
                exclude = ('title',)

        self.assertEqual(len(F.declared_filters), 1)
        self.assertEqual(len(F.base_filters), 2)
        self.assertListEqual(list(F.base_filters),
                             ['username', 'price'])

    def test_filterset_class_inheritance(self):
        class F(FilterSet):
            class Meta:
                model = Book

        class G(F):
            pass
        self.assertEqual(set(F.base_filters), set(G.base_filters))

        class F(FilterSet):
            other = CharFilter

            class Meta:
                model = Book

        class G(F):
            pass
        self.assertEqual(set(F.base_filters), set(G.base_filters))

    def test_abstract_model_inheritance(self):
        class F(FilterSet):
            class Meta:
                model = Restaurant

        self.assertEqual(set(F.base_filters), set(['name', 'serves_pizza']))

        class F(FilterSet):
            class Meta:
                model = Restaurant
                fields = ['name', 'serves_pizza']

        self.assertEqual(set(F.base_filters), set(['name', 'serves_pizza']))

    def test_custom_field_ignored(self):
        class F(FilterSet):
            class Meta:
                model = NetworkSetting

        self.assertEqual(list(F.base_filters.keys()), ['ip'])

    def test_custom_field_gets_filter_from_override(self):
        class F(FilterSet):
            filter_overrides = {
                SubnetMaskField: {'filter_class': CharFilter}}

            class Meta:
                model = NetworkSetting

        self.assertEqual(list(F.base_filters.keys()), ['ip', 'mask'])

    def test_filterset_for_proxy_model(self):
        class F(FilterSet):
            class Meta:
                model = User

        class ProxyF(FilterSet):
            class Meta:
                model = AdminUser

        self.assertEqual(list(F.base_filters), list(ProxyF.base_filters))

    def test_filterset_for_mti_model(self):
        class F(FilterSet):
            class Meta:
                model = Account

        class FtiF(FilterSet):
            class Meta:
                model = BankAccount

        # fails due to 'account_ptr' getting picked up
        self.assertEqual(
            list(F.base_filters) + ['amount_saved'],
            list(FtiF.base_filters))


class FilterSetInstantiationTests(TestCase):

    def test_creating_instance(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username']

        f = F()
        self.assertFalse(f.is_bound)
        self.assertIsNotNone(f.queryset)
        self.assertEqual(len(f.filters), len(F.base_filters))
        for name, filter_ in f.filters.items():
            self.assertEqual(
                filter_.model,
                User,
                "%s does not have model set correctly" % name)

    def test_creating_bound_instance(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username']

        f = F({'username': 'username'})
        self.assertTrue(f.is_bound)

    def test_creating_with_queryset(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username']

        m = mock.Mock()
        f = F(queryset=m)
        self.assertEqual(f.queryset, m)


class FilterSetOrderingTests(TestCase):

    def setUp(self):
        self.alex = User.objects.create(username='alex', status=1)
        self.jacob = User.objects.create(username='jacob', status=2)
        self.aaron = User.objects.create(username='aaron', status=2)
        self.carl = User.objects.create(username='carl', status=0)
        # user_ids = list(User.objects.all().values_list('pk', flat=True))
        self.qs = User.objects.all().order_by('id')

    def test_ordering_when_unbound(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']

        f = F(queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['carl', 'alex', 'jacob', 'aaron'], lambda o: o.username)

    def test_ordering(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['username', 'status']

        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['aaron', 'alex', 'carl', 'jacob'], lambda o: o.username)

        f = F({'o': 'status'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['carl', 'alex', 'jacob', 'aaron'], lambda o: o.username)

    def test_ordering_on_unknown_value(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']

        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, [], lambda o: o.username)

    def test_ordering_on_unknown_value_results_in_default_ordering_without_strict(self):
        class F(FilterSet):
            strict = STRICTNESS.IGNORE

            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']

        self.assertFalse(F.strict)
        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['alex', 'jacob', 'aaron', 'carl'], lambda o: o.username)

    def test_ordering_on_unknown_value_results_in_default_ordering_with_strict_raise(self):
        class F(FilterSet):
            strict = STRICTNESS.RAISE_VALIDATION_ERROR

            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']

        f = F({'o': 'username'}, queryset=self.qs)
        with self.assertRaises(ValidationError) as excinfo:
            f.qs.all()
        self.assertEqual(excinfo.exception.message_dict,
                         {'o': ['Select a valid choice. username is not one '
                                'of the available choices.']})

        # No default order_by should get applied.
        f = F({}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['alex', 'jacob', 'aaron', 'carl'], lambda o: o.username)

    def test_ordering_on_different_field(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True

        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['aaron', 'alex', 'carl', 'jacob'], lambda o: o.username)

        f = F({'o': 'status'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['carl', 'alex', 'jacob', 'aaron'], lambda o: o.username)

    def test_ordering_uses_filter_name(self):
        class F(FilterSet):
            account = CharFilter(name='username')
            class Meta:
                model = User
                fields = ['account', 'status']
                order_by = True

        f = F({'o': 'account'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['aaron', 'alex', 'carl', 'jacob'], lambda o: o.username)

    def test_reverted_ordering_uses_filter_name(self):
        class F(FilterSet):
            account = CharFilter(name='username')
            class Meta:
                model = User
                fields = ['account', 'status']
                order_by = True

        f = F({'o': '-account'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['jacob', 'carl', 'alex', 'aaron'], lambda o: o.username)

    def test_ordering_with_overridden_field_name(self):
        """
        Set the `order_by_field` on the queryset and ensure that the
        field name is respected.
        """
        class F(FilterSet):
            order_by_field = 'order'

            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']

        f = F({'order': 'status'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['carl', 'alex', 'jacob', 'aaron'], lambda o: o.username)

    def test_ordering_descending_set(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['username', '-username']

        f = F({'o': '-username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['jacob', 'carl', 'alex', 'aaron'], lambda o: o.username)

    def test_ordering_descending_unset(self):
        """ Test ordering descending works when order_by=True. """
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True

        f = F({'o': '-username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['jacob', 'carl', 'alex', 'aaron'], lambda o: o.username)

    def test_custom_ordering(self):

        class F(FilterSet):
            debug = True
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['username', 'status']

            def get_order_by(self, order_choice):
                if order_choice == 'status':
                    return ['status', 'username']
                return super(F, self).get_order_by(order_choice)

        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['aaron', 'alex', 'carl', 'jacob'], lambda o: o.username)

        f = F({'o': 'status'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['carl', 'alex', 'aaron', 'jacob'], lambda o: o.username)



class FilterSetTogetherTests(TestCase):

    def setUp(self):
        self.alex = User.objects.create(username='alex', status=1)
        self.jacob = User.objects.create(username='jacob', status=2)
        self.qs = User.objects.all().order_by('id')

    def test_fields_set(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status', 'is_active', 'first_name']
                together = [
                    ('username', 'status'),
                    ('first_name', 'is_active'),
                ]

        f = F({}, queryset=self.qs)
        self.assertEqual(f.qs.count(), 2)
        f = F({'username': 'alex'}, queryset=self.qs)
        self.assertEqual(f.qs.count(), 0)
        f = F({'username': 'alex', 'status': 1}, queryset=self.qs)
        self.assertEqual(f.qs.count(), 1)
        self.assertQuerysetEqual(f.qs, [self.alex.pk], lambda o: o.pk)

    def test_single_fields_set(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                together = ['username', 'status']

        f = F({}, queryset=self.qs)
        self.assertEqual(f.qs.count(), 2)
        f = F({'username': 'alex'}, queryset=self.qs)
        self.assertEqual(f.qs.count(), 0)
        f = F({'username': 'alex', 'status': 1}, queryset=self.qs)
        self.assertEqual(f.qs.count(), 1)
        self.assertQuerysetEqual(f.qs, [self.alex.pk], lambda o: o.pk)
