import mock
import unittest

from django.db import models
from django.test import TestCase

from django_filters.exceptions import FieldLookupError
from django_filters.filters import (
    BaseInFilter,
    BaseRangeFilter,
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    DateRangeFilter,
    Filter,
    FilterMethod,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    NumberFilter,
    UUIDFilter
)
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS, FilterSet
from django_filters.widgets import BooleanWidget

from .models import (
    Account,
    AdminUser,
    Article,
    BankAccount,
    Book,
    Business,
    Comment,
    DirectedNode,
    NetworkSetting,
    Node,
    Profile,
    Restaurant,
    SubnetMaskField,
    User,
    UUIDTestModel,
    Worker
)
from .utils import MockQuerySet


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
        self.assertEqual(result.field_name, 'username')

    def test_filter_found_for_uuidfield(self):
        f = UUIDTestModel._meta.get_field('uuid')
        result = FilterSet.filter_for_field(f, 'uuid')
        self.assertIsInstance(result, UUIDFilter)
        self.assertEqual(result.field_name, 'uuid')

    def test_filter_found_for_autofield(self):
        f = User._meta.get_field('id')
        result = FilterSet.filter_for_field(f, 'id')
        self.assertIsInstance(result, NumberFilter)
        self.assertEqual(result.field_name, 'id')

    def test_field_with_extras(self):
        f = User._meta.get_field('favorite_books')
        result = FilterSet.filter_for_field(f, 'favorite_books')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.field_name, 'favorite_books')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Book)

    def test_field_with_choices(self):
        f = User._meta.get_field('status')
        result = FilterSet.filter_for_field(f, 'status')
        self.assertIsInstance(result, ChoiceFilter)
        self.assertEqual(result.field_name, 'status')
        self.assertTrue('choices' in result.extra)
        self.assertIsNotNone(result.extra['choices'])

    def test_field_that_is_subclassed(self):
        f = User._meta.get_field('first_name')
        result = FilterSet.filter_for_field(f, 'first_name')
        self.assertIsInstance(result, CharFilter)

    def test_unknown_field_type_error(self):
        f = NetworkSetting._meta.get_field('mask')

        with self.assertRaises(AssertionError) as excinfo:
            FilterSet.filter_for_field(f, 'mask')

        self.assertIn(
            "FilterSet resolved field 'mask' with 'exact' lookup "
            "to an unrecognized field type SubnetMaskField",
            excinfo.exception.args[0])

    def test_symmetrical_selfref_m2m_field(self):
        f = Node._meta.get_field('adjacents')
        result = FilterSet.filter_for_field(f, 'adjacents')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.field_name, 'adjacents')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Node)

    def test_non_symmetrical_selfref_m2m_field(self):
        f = DirectedNode._meta.get_field('outbound_nodes')
        result = FilterSet.filter_for_field(f, 'outbound_nodes')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.field_name, 'outbound_nodes')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, DirectedNode)

    def test_m2m_field_with_through_model(self):
        f = Business._meta.get_field('employees')
        result = FilterSet.filter_for_field(f, 'employees')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.field_name, 'employees')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Worker)

    def test_transformed_lookup_expr(self):
        f = Comment._meta.get_field('date')
        result = FilterSet.filter_for_field(f, 'date', 'year__gte')
        self.assertIsInstance(result, NumberFilter)
        self.assertEqual(result.field_name, 'date')

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
            class Meta:
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


class ReverseFilterSetFilterForFieldTests(TestCase):
    # Test reverse relationships for `filter_for_field`

    def test_reverse_o2o_relationship(self):
        f = Account._meta.get_field('profile')
        result = FilterSet.filter_for_field(f, 'profile')
        self.assertIsInstance(result, ModelChoiceFilter)
        self.assertEqual(result.field_name, 'profile')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Profile)

    def test_reverse_fk_relationship(self):
        f = User._meta.get_field('comments')
        result = FilterSet.filter_for_field(f, 'comments')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.field_name, 'comments')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Comment)

    def test_reverse_m2m_relationship(self):
        f = Book._meta.get_field('lovers')
        result = FilterSet.filter_for_field(f, 'lovers')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.field_name, 'lovers')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, User)

    def test_reverse_non_symmetrical_selfref_m2m_field(self):
        f = DirectedNode._meta.get_field('inbound_nodes')
        result = FilterSet.filter_for_field(f, 'inbound_nodes')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.field_name, 'inbound_nodes')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, DirectedNode)

    def test_reverse_m2m_field_with_through_model(self):
        f = Worker._meta.get_field('employers')
        result = FilterSet.filter_for_field(f, 'employers')
        self.assertIsInstance(result, ModelMultipleChoiceFilter)
        self.assertEqual(result.field_name, 'employers')
        self.assertTrue('queryset' in result.extra)
        self.assertIsNotNone(result.extra['queryset'])
        self.assertEqual(result.extra['queryset'].model, Business)

    def test_reverse_relationship_lookup_expr(self):
        f = Book._meta.get_field('lovers')
        result = FilterSet.filter_for_field(f, 'lovers', 'isnull')
        self.assertIsInstance(result, BooleanFilter)
        self.assertEqual(result.field_name, 'lovers')
        self.assertEqual(result.lookup_expr, 'isnull')


class FilterSetFilterForReverseFieldTests(TestCase):

    def test_method_raises_assertion(self):
        msg = ("`F.filter_for_reverse_field` has been removed. "
               "`F.filter_for_field` now generates filters for reverse fields.")

        with self.assertRaisesMessage(AssertionError, msg):
            class F(FilterSet):
                @classmethod
                def filter_for_reverse_field(cls, field, field_name):
                    pass


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
                fields = '__all__'

        self.assertEqual(len(F.declared_filters), 0)
        self.assertEqual(len(F.base_filters), 3)
        self.assertListEqual(list(F.base_filters),
                             ['title', 'price', 'average_rating'])

    def test_model_no_fields_or_exclude(self):
        with self.assertRaises(AssertionError) as excinfo:
            class F(FilterSet):
                class Meta:
                    model = Book

        self.assertIn(
            "Setting 'Meta.model' without either 'Meta.fields' or 'Meta.exclude'",
            str(excinfo.exception)
        )

    def test_model_fields_empty(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = []

        self.assertEqual(len(F.declared_filters), 0)
        self.assertEqual(len(F.base_filters), 0)
        self.assertListEqual(list(F.base_filters), [])

    def test_model_exclude_empty(self):
        # equivalent to fields = '__all__'
        class F(FilterSet):
            class Meta:
                model = Book
                exclude = []

        self.assertEqual(len(F.declared_filters), 0)
        self.assertEqual(len(F.base_filters), 3)
        self.assertListEqual(list(F.base_filters),
                             ['title', 'price', 'average_rating'])

    def test_declared_and_model_derived(self):
        class F(FilterSet):
            username = CharFilter()

            class Meta:
                model = Book
                fields = '__all__'

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
                    fields = ('username', 'price', 'other', 'another')

        self.assertEqual(
            str(excinfo.exception),
            "'Meta.fields' contains fields that are not defined on this FilterSet: "
            "other, another"
        )

    def test_meta_fields_dictionary_containing_unknown(self):
        with self.assertRaises(TypeError):
            class F(FilterSet):

                class Meta:
                    model = Book
                    fields = {'id': ['exact'],
                              'title': ['exact'],
                              'other': ['exact'],
                              }

    def test_meta_fields_invalid_lookup(self):
        # We want to ensure that non existent lookups (or just simple misspellings)
        # throw a useful exception containg the field and lookup expr.
        with self.assertRaises(FieldLookupError) as context:
            class F(FilterSet):
                class Meta:
                    model = User
                    fields = {'username': ['flub']}

        exc = str(context.exception)
        self.assertIn('tests.User.username', exc)
        self.assertIn('flub', exc)

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

    def test_meta_exlude_with_no_fields(self):
        class F(FilterSet):
            class Meta:
                model = Book
                exclude = ('price', )

        self.assertEqual(len(F.declared_filters), 0)
        self.assertEqual(len(F.base_filters), 2)
        self.assertListEqual(list(F.base_filters),
                             ['title', 'average_rating'])

    def test_filterset_class_inheritance(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = '__all__'

        class G(F):
            pass
        self.assertEqual(set(F.base_filters), set(G.base_filters))

        class F(FilterSet):
            other = CharFilter

            class Meta:
                model = Book
                fields = '__all__'

        class G(F):
            pass
        self.assertEqual(set(F.base_filters), set(G.base_filters))

    def test_abstract_model_inheritance(self):
        class F(FilterSet):
            class Meta:
                model = Restaurant
                fields = '__all__'

        self.assertEqual(set(F.base_filters), set(['name', 'serves_pizza']))

        class F(FilterSet):
            class Meta:
                model = Restaurant
                fields = ['name', 'serves_pizza']

        self.assertEqual(set(F.base_filters), set(['name', 'serves_pizza']))

    def test_custom_field_gets_filter_from_override(self):
        class F(FilterSet):
            class Meta:
                model = NetworkSetting
                fields = '__all__'

                filter_overrides = {
                    SubnetMaskField: {'filter_class': CharFilter}
                }

        self.assertEqual(list(F.base_filters.keys()), ['ip', 'mask', 'cidr'])

    def test_custom_declared_field_no_warning(self):
        class F(FilterSet):
            mask = CharFilter()

            class Meta:
                model = NetworkSetting
                fields = ['mask']

        self.assertEqual(list(F.base_filters.keys()), ['mask'])

    def test_filterset_for_proxy_model(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = '__all__'

        class ProxyF(FilterSet):
            class Meta:
                model = AdminUser
                fields = '__all__'

        self.assertEqual(list(F.base_filters), list(ProxyF.base_filters))

    def test_filterset_for_mti_model(self):
        class F(FilterSet):
            class Meta:
                model = Account
                fields = '__all__'

        class FtiF(FilterSet):
            class Meta:
                model = BankAccount
                fields = '__all__'

        # fails due to 'account_ptr' getting picked up
        self.assertEqual(
            list(F.base_filters) + ['amount_saved'],
            list(FtiF.base_filters))

    def test_declared_filter_disabling(self):
        class Parent(FilterSet):
            f1 = CharFilter()
            f2 = CharFilter()

        class Child(Parent):
            f1 = None

        class Grandchild(Child):
            pass

        self.assertEqual(len(Parent.base_filters), 2)
        self.assertEqual(len(Child.base_filters), 1)
        self.assertEqual(len(Grandchild.base_filters), 1)


class FilterSetInstantiationTests(TestCase):

    class F(FilterSet):
        class Meta:
            model = User
            fields = ['username']

    def test_creating_instance(self):
        f = self.F()
        self.assertFalse(f.is_bound)
        self.assertIsNotNone(f.queryset)
        self.assertEqual(len(f.filters), len(self.F.base_filters))
        for name, filter_ in f.filters.items():
            self.assertEqual(
                filter_.model,
                User,
                "%s does not have model set correctly" % name)

    def test_creating_bound_instance(self):
        f = self.F({'username': 'username'})
        self.assertTrue(f.is_bound)

    def test_creating_with_queryset(self):
        m = mock.Mock()
        f = self.F(queryset=m)
        self.assertEqual(f.queryset, m)

    def test_creating_with_request(self):
        m = mock.Mock()
        f = self.F(request=m)
        self.assertEqual(f.request, m)


class FilterSetQuerysetTests(TestCase):

    class F(FilterSet):
        invalid = CharFilter(method=lambda *args: None)

        class Meta:
            model = User
            fields = ['username', 'invalid']

    def test_filter_queryset_called_once(self):
        m = MockQuerySet()
        f = self.F({'username': 'bob'}, queryset=m)

        with mock.patch.object(f, 'filter_queryset',
                               wraps=f.filter_queryset) as fn:
            f.qs
            fn.assert_called_once_with(m.all())
            f.qs
            fn.assert_called_once_with(m.all())

    def test_get_form_class_called_once(self):
        f = self.F()

        with mock.patch.object(f, 'get_form_class',
                               wraps=f.get_form_class) as fn:
            f.form
            fn.assert_called_once()
            f.form
            fn.assert_called_once()

    def test_qs_caching(self):
        m = mock.Mock()
        f = self.F(queryset=m)

        self.assertIs(f.qs, m.all())
        self.assertIs(f.qs, f.qs)

    def test_form_caching(self):
        f = self.F()

        self.assertIs(f.form, f.form)

    def test_qs_triggers_form_validation(self):
        m = MockQuerySet()
        f = self.F({'username': 'bob'}, queryset=m)

        with mock.patch.object(f.form, 'full_clean',
                               wraps=f.form.full_clean) as fn:
            fn.assert_not_called()
            f.qs
            fn.assert_called()

    def test_filters_must_return_queryset(self):
        m = MockQuerySet()
        f = self.F({'invalid': 'result'}, queryset=m)

        msg = "Expected 'F.invalid' to return a QuerySet, but got a NoneType instead."
        with self.assertRaisesMessage(AssertionError, msg):
            f.qs


# test filter.method here, as it depends on its parent FilterSet
class FilterMethodTests(TestCase):

    def test_none(self):
        # use a mock to bypass bound/unbound method equality
        class TestFilter(Filter):
            filter = mock.Mock()

        f = TestFilter(method=None)
        self.assertIsNone(f.method)

        # passing method=None should not modify filter function
        self.assertIs(f.filter, TestFilter.filter)

    def test_method_name(self):
        class F(FilterSet):
            f = Filter(method='filter_f')

            def filter_f(self, qs, name, value):
                pass

        f = F({}, queryset=User.objects.all())
        self.assertEqual(f.filters['f'].method, 'filter_f')
        self.assertEqual(f.filters['f'].filter.method, f.filter_f)
        self.assertIsInstance(f.filters['f'].filter, FilterMethod)

    def test_method_callable(self):
        def filter_f(qs, name, value):
            pass

        class F(FilterSet):
            f = Filter(method=filter_f)

        f = F({}, queryset=User.objects.all())
        self.assertEqual(f.filters['f'].method, filter_f)
        self.assertEqual(f.filters['f'].filter.method, filter_f)
        self.assertIsInstance(f.filters['f'].filter, FilterMethod)

    def test_request_available_during_method_called(self):
        class F(FilterSet):
            f = Filter(method='filter_f')

            def filter_f(self, qs, name, value):
                # call mock request object to prove self.request can be accessed
                self.request()

        m = mock.Mock()
        f = F({}, queryset=User.objects.all(), request=m)
        # call the filter
        f.filters['f'].filter.method(User.objects.all(), 'f', '')
        m.assert_called_once_with()

    def test_method_with_overridden_filter(self):
        # Some filter classes override the base filter() method. We need
        # to ensure that passing a method argument still works correctly
        class F(FilterSet):
            f = DateRangeFilter(method='filter_f')

            def filter_f(self, qs, name, value):
                pass

        f = F({}, queryset=User.objects.all())
        self.assertEqual(f.filters['f'].method, 'filter_f')
        self.assertEqual(f.filters['f'].filter.method, f.filter_f)

    def test_parent_unresolvable(self):
        f = Filter(method='filter_f')
        with self.assertRaises(AssertionError) as w:
            f.filter(User.objects.all(), 0)

        self.assertIn("'None'", str(w.exception))
        self.assertIn('parent', str(w.exception))
        self.assertIn('filter_f', str(w.exception))

    def test_method_self_is_parent(self):
        # Ensure the method isn't 're-parented' on the `FilterMethod` helper class.
        # Filter methods should have access to the filterset's properties.
        request = MockQuerySet()

        class F(FilterSet):
            f = CharFilter(method='filter_f')

            class Meta:
                model = User
                fields = []

            def filter_f(inner_self, qs, name, value):
                self.assertIsInstance(inner_self, F)
                self.assertIs(inner_self.request, request)
                return qs

        F({'f': 'foo'}, request=request, queryset=User.objects.all()).qs

    def test_method_unresolvable(self):
        class F(FilterSet):
            f = Filter(method='filter_f')

        f = F({}, queryset=User.objects.all())

        with self.assertRaises(AssertionError) as w:
            f.filters['f'].filter(User.objects.all(), 0)

        self.assertIn('%s.%s' % (F.__module__, F.__name__), str(w.exception))
        self.assertIn('.filter_f()', str(w.exception))

    def test_method_uncallable(self):
        class F(FilterSet):
            f = Filter(method='filter_f')
            filter_f = 4

        f = F({}, queryset=User.objects.all())

        with self.assertRaises(AssertionError) as w:
            f.filters['f'].filter(User.objects.all(), 0)

        self.assertIn('%s.%s' % (F.__module__, F.__name__), str(w.exception))
        self.assertIn('.filter_f()', str(w.exception))

    def test_method_set_unset(self):
        # use a mock to bypass bound/unbound method equality
        class TestFilter(Filter):
            filter = mock.Mock()

        f = TestFilter(method='filter_f')
        self.assertEqual(f.method, 'filter_f')
        self.assertIsInstance(f.filter, FilterMethod)

        # setting None should revert to Filter.filter
        f.method = None
        self.assertIsNone(f.method)
        self.assertIs(f.filter, TestFilter.filter)


class MiscFilterSetTests(TestCase):

    def test_no__getitem__(self):
        # The DTL processes variable lookups by the following rules:
        # https://docs.djangoproject.com/en/stable/ref/templates/language/#variables
        # A __getitem__ implementation precedes normal attribute access, and in
        # the case of #58, will force the queryset to evaluate when it should
        # not (eg, when rendering a blank form).
        self.assertFalse(hasattr(FilterSet, '__getitem__'))

    def test_no_qs_proxying(self):
        # The FilterSet should not proxy .qs methods - just access .qs directly
        self.assertFalse(hasattr(FilterSet, '__len__'))
        self.assertFalse(hasattr(FilterSet, '__iter__'))
