from __future__ import absolute_import
from __future__ import unicode_literals

import mock

from django.db import models
from django.utils import unittest
from django.test import TestCase

from django_filters.filterset import FilterSet
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS
from django_filters.filterset import get_model_field
from django_filters.filters import CharFilter
from django_filters.filters import ChoiceFilter
from django_filters.filters import ModelChoiceFilter
from django_filters.filters import ModelMultipleChoiceFilter

from .models import User
from .models import AdminUser
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
from .models import Business


class HelperMethodsTests(TestCase):

    @unittest.skip('todo')
    def test_get_declared_filters(self):
        pass

    def test_get_model_field(self):
        result = get_model_field(User, 'unknown__name')
        self.assertIsNone(result)

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
            models.IPAddressField,
            models.NullBooleanField,
            models.PositiveIntegerField,
            models.PositiveSmallIntegerField,
            models.SlugField,
            models.SmallIntegerField,
            models.TextField,
            models.TimeField,
            models.URLField,
            models.ForeignKey,
            models.OneToOneField,
            models.ManyToManyField,
        ]
        msg = "%s expected to be found in FILTER_FOR_DBFIELD_DEFAULTS"

        for m in to_check:
            self.assertIn(m, FILTER_FOR_DBFIELD_DEFAULTS, msg % m.__name__)

    def test_expected_db_fields_do_not_get_filters(self):
        to_check = [
            models.Field,
            models.AutoField,
            models.BigIntegerField,
            models.GenericIPAddressField,
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

    def test_filter_not_found_for_field(self):
        f = User._meta.get_field('id')
        result = FilterSet.filter_for_field(f, 'id')
        self.assertIsNone(result)

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

    @unittest.skip('todo')
    def test_filter_overrides(self):
        pass


class FilterSetFilterForReverseFieldTests(TestCase):

    def test_reverse_o2o_relationship(self):
        f = Account._meta.get_field_by_name('profile')[0]
        result = FilterSet.filter_for_reverse_field(f, 'profile')
        self.assertIsInstance(result, ModelChoiceFilter)
        self.assertEqual(result.name, 'profile')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Profile)

    def test_reverse_fk_relationship(self):
        f = User._meta.get_field_by_name('comments')[0]
        result = FilterSet.filter_for_reverse_field(f, 'comments')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'comments')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Comment)

    def test_reverse_m2m_relationship(self):
        f = Book._meta.get_field_by_name('lovers')[0]
        result = FilterSet.filter_for_reverse_field(f, 'lovers')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'lovers')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, User)

    def test_reverse_non_symmetrical_selfref_m2m_field(self):
        f = DirectedNode._meta.get_field_by_name('inbound_nodes')[0]
        result = FilterSet.filter_for_reverse_field(f, 'inbound_nodes')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.name, 'inbound_nodes')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, DirectedNode)

    def test_reverse_m2m_field_with_through_model(self):
        f = Worker._meta.get_field_by_name('employers')[0]
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

    def test_meta_fields_containing_unknown(self):
        with self.assertRaises(TypeError):
            class F(FilterSet):
                username = CharFilter()

                class Meta:
                    model = Book
                    fields = ('username', 'price', 'other')

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

    @unittest.expectedFailure
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

    def test_ordering_unset(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']
        
        f = F(queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['alex', 'jacob', 'aaron', 'carl'], lambda o: o.username)

    def test_ordering(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']
        
        f = F({'o': 'status'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['carl', 'alex', 'jacob', 'aaron'], lambda o: o.username)

    def test_ordering_on_unknown_value_is_ignored(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']
        
        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['alex', 'jacob', 'aaron', 'carl'], lambda o: o.username)

    def test_ordering_on_differnt_field(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True
        
        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['aaron', 'alex', 'carl', 'jacob'], lambda o: o.username)

    @unittest.skip('todo')
    def test_ordering_uses_filter_name(self):
        class F(FilterSet):
            account = CharFilter(name='username')

            class Meta:
                model = User
                fields = ['account', 'status']
                order_by = True
        
        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['aaron', 'alex', 'carl', 'jacob'], lambda o: o.username)

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

