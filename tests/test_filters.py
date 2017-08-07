# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict
from datetime import date, time, timedelta, datetime
import inspect
import mock

from django import forms
from django.test import TestCase, override_settings
from django.utils import translation
from django.utils.translation import ugettext as _

from django_filters import filters, widgets
from django_filters.fields import (
    Lookup,
    RangeField,
    DateRangeField,
    DateTimeRangeField,
    TimeRangeField,
    LookupTypeField,
    BaseCSVField)
from django_filters.filters import (
    Filter,
    CharFilter,
    BooleanFilter,
    ChoiceFilter,
    MultipleChoiceFilter,
    TypedMultipleChoiceFilter,
    DateFilter,
    DateTimeFilter,
    TimeFilter,
    DurationFilter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    NumberFilter,
    NumericRangeFilter,
    RangeFilter,
    DateRangeFilter,
    DateFromToRangeFilter,
    DateTimeFromToRangeFilter,
    TimeRangeFilter,
    AllValuesFilter,
    BaseCSVFilter,
    BaseInFilter,
    BaseRangeFilter,
    UUIDFilter,
    OrderingFilter,
    LOOKUP_TYPES)

from tests.models import Book, User


class ModuleImportTests(TestCase):
    def is_filter(self, name, value):
        return (
            isinstance(value, type) and issubclass(value, Filter)
        )

    def test_imports(self):
        # msg = "Expected `filters.%s` to be imported in `filters.__all__`"
        filter_classes = [
            key for key, value
            in inspect.getmembers(filters)
            if isinstance(value, type) and issubclass(value, Filter)
        ]

        # sanity check
        self.assertIn('Filter', filter_classes)
        self.assertIn('BooleanFilter', filter_classes)

        for f in filter_classes:
            self.assertIn(f, filters.__all__)


class FilterTests(TestCase):

    def test_creation(self):
        f = Filter()
        self.assertEqual(f.lookup_expr, 'exact')
        self.assertEqual(f.exclude, False)

    def test_creation_order(self):
        f = Filter()
        f2 = Filter()
        self.assertTrue(f2.creation_counter > f.creation_counter)

    def test_default_field(self):
        f = Filter()
        field = f.field
        self.assertIsInstance(field, forms.Field)

    def test_field_with_single_lookup_expr(self):
        f = Filter(lookup_expr='iexact')
        field = f.field
        self.assertIsInstance(field, forms.Field)

    def test_field_with_none_lookup_expr(self):
        f = Filter(lookup_expr=None)
        field = f.field
        self.assertIsInstance(field, LookupTypeField)
        choice_field = field.fields[1]
        self.assertEqual(len(choice_field.choices), len(LOOKUP_TYPES))

    def test_field_with_lookup_expr_and_exlusion(self):
        f = Filter(lookup_expr=None, exclude=True)
        field = f.field
        self.assertIsInstance(field, LookupTypeField)

    def test_field_with_list_lookup_expr(self):
        f = Filter(lookup_expr=('istartswith', 'iendswith'))
        field = f.field
        self.assertIsInstance(field, LookupTypeField)
        choice_field = field.fields[1]
        self.assertEqual(len(choice_field.choices), 2)

    def test_field_params(self):
        with mock.patch.object(Filter, 'field_class',
                               spec=['__call__']) as mocked:
            f = Filter(name='somefield', label='somelabel',
                       widget='somewidget')
            f.field
            mocked.assert_called_once_with(required=False,
                                           label='somelabel',
                                           widget='somewidget')

    def test_field_extra_params(self):
        with mock.patch.object(Filter, 'field_class',
                               spec=['__call__']) as mocked:
            f = Filter(someattr='someattr')
            f.field
            mocked.assert_called_once_with(required=mock.ANY,
                                           label=mock.ANY,
                                           widget=mock.ANY,
                                           someattr='someattr')

    def test_field_with_required_filter(self):
        with mock.patch.object(Filter, 'field_class',
                               spec=['__call__']) as mocked:
            f = Filter(required=True)
            f.field
            mocked.assert_called_once_with(required=True,
                                           label=mock.ANY,
                                           widget=mock.ANY)

    def test_filtering(self):
        qs = mock.Mock(spec=['filter'])
        f = Filter()
        result = f.filter(qs, 'value')
        qs.filter.assert_called_once_with(None__exact='value')
        self.assertNotEqual(qs, result)

    def test_filtering_exclude(self):
        qs = mock.Mock(spec=['filter', 'exclude'])
        f = Filter(exclude=True)
        result = f.filter(qs, 'value')
        qs.exclude.assert_called_once_with(None__exact='value')
        self.assertNotEqual(qs, result)

    def test_filtering_uses_name(self):
        qs = mock.Mock(spec=['filter'])
        f = Filter(name='somefield')
        f.filter(qs, 'value')
        result = qs.filter.assert_called_once_with(somefield__exact='value')
        self.assertNotEqual(qs, result)

    def test_filtering_skipped_with_blank_value(self):
        qs = mock.Mock()
        f = Filter()
        result = f.filter(qs, '')
        self.assertListEqual(qs.method_calls, [])
        self.assertEqual(qs, result)

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock()
        f = Filter()
        result = f.filter(qs, None)
        self.assertListEqual(qs.method_calls, [])
        self.assertEqual(qs, result)

    def test_filtering_with_list_value(self):
        qs = mock.Mock(spec=['filter'])
        f = Filter(name='somefield', lookup_expr=['some_lookup_expr'])
        result = f.filter(qs, Lookup('value', 'some_lookup_expr'))
        qs.filter.assert_called_once_with(somefield__some_lookup_expr='value')
        self.assertNotEqual(qs, result)

    def test_filtering_skipped_with_list_value_with_blank(self):
        qs = mock.Mock()
        f = Filter(name='somefield', lookup_expr=['some_lookup_expr'])
        result = f.filter(qs, Lookup('', 'some_lookup_expr'))
        self.assertListEqual(qs.method_calls, [])
        self.assertEqual(qs, result)

    def test_filtering_skipped_with_list_value_with_blank_lookup(self):
        return  # Now field is required to provide valid lookup_expr if it provides any
        qs = mock.Mock(spec=['filter'])
        f = Filter(name='somefield', lookup_expr=None)
        result = f.filter(qs, Lookup('value', ''))
        qs.filter.assert_called_once_with(somefield__exact='value')
        self.assertNotEqual(qs, result)

    def test_filter_using_method(self):
        qs = mock.NonCallableMock(spec=[])
        method = mock.Mock()
        f = Filter(method=method)
        result = f.filter(qs, 'value')
        method.assert_called_once_with(qs, None, 'value')
        self.assertNotEqual(qs, result)

    def test_filtering_uses_distinct(self):
        qs = mock.Mock(spec=['filter', 'distinct'])
        f = Filter(name='somefield', distinct=True)
        f.filter(qs, 'value')
        result = qs.distinct.assert_called_once_with()
        self.assertNotEqual(qs, result)


class CustomFilterWithBooleanCheckTests(TestCase):

    def setUp(self):
        super(CustomFilterWithBooleanCheckTests, self).setUp()

        class CustomTestFilter(Filter):
            def filter(self_, qs, value):
                if not value:
                    return qs
                return super(CustomTestFilter, self_).filter(qs, value)

        self.test_filter_class = CustomTestFilter

    def test_lookup_false(self):
        qs = mock.Mock(spec=['filter'])
        f = self.test_filter_class(name='somefield')
        result = f.filter(qs, Lookup('', 'exact'))
        self.assertEqual(qs, result)

    def test_lookup_true(self):
        qs = mock.Mock(spec=['filter'])
        f = self.test_filter_class(name='somefield')
        result = f.filter(qs, Lookup('somesearch', 'exact'))
        qs.filter.assert_called_once_with(somefield__exact='somesearch')
        self.assertNotEqual(qs, result)


class CharFilterTests(TestCase):

    def test_default_field(self):
        f = CharFilter()
        field = f.field
        self.assertIsInstance(field, forms.CharField)


class UUIDFilterTests(TestCase):

    def test_default_field(self):
        f = UUIDFilter()
        field = f.field
        self.assertIsInstance(field, forms.UUIDField)


class BooleanFilterTests(TestCase):

    def test_default_field(self):
        f = BooleanFilter()
        field = f.field
        self.assertIsInstance(field, forms.NullBooleanField)

    def test_filtering(self):
        qs = mock.Mock(spec=['filter'])
        f = BooleanFilter(name='somefield')
        result = f.filter(qs, True)
        qs.filter.assert_called_once_with(somefield__exact=True)
        self.assertNotEqual(qs, result)

    def test_filtering_exclude(self):
        qs = mock.Mock(spec=['exclude'])
        f = BooleanFilter(name='somefield', exclude=True)
        result = f.filter(qs, True)
        qs.exclude.assert_called_once_with(somefield__exact=True)
        self.assertNotEqual(qs, result)

    def test_filtering_skipped_with_blank_value(self):
        qs = mock.Mock()
        f = BooleanFilter(name='somefield')
        result = f.filter(qs, '')
        self.assertListEqual(qs.method_calls, [])
        self.assertEqual(qs, result)

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock()
        f = BooleanFilter(name='somefield')
        result = f.filter(qs, None)
        self.assertListEqual(qs.method_calls, [])
        self.assertEqual(qs, result)

    def test_filtering_lookup_expr(self):
        qs = mock.Mock(spec=['filter'])
        f = BooleanFilter(name='somefield', lookup_expr='isnull')
        result = f.filter(qs, True)
        qs.filter.assert_called_once_with(somefield__isnull=True)
        self.assertNotEqual(qs, result)


class ChoiceFilterTests(TestCase):

    def test_default_field(self):
        f = ChoiceFilter()
        field = f.field
        self.assertIsInstance(field, forms.ChoiceField)

    def test_empty_choice(self):
        # default value
        f = ChoiceFilter(choices=[('a', 'a')])
        self.assertEqual(f.field.choices, [
            ('', '---------'),
            ('a', 'a'),
        ])

        # set value, allow blank label
        f = ChoiceFilter(choices=[('a', 'a')], empty_label='')
        self.assertEqual(f.field.choices, [
            ('', ''),
            ('a', 'a'),
        ])

        # disable empty choice w/ None
        f = ChoiceFilter(choices=[('a', 'a')], empty_label=None)
        self.assertEqual(f.field.choices, [
            ('a', 'a'),
        ])

    def test_null_choice(self):
        # default is to be disabled
        f = ChoiceFilter(choices=[('a', 'a')], )
        self.assertEqual(f.field.choices, [
            ('', '---------'),
            ('a', 'a'),
        ])

        # set label, allow blank label
        f = ChoiceFilter(choices=[('a', 'a')], null_label='')
        self.assertEqual(f.field.choices, [
            ('', '---------'),
            ('null', ''),
            ('a', 'a'),
        ])

        # set null value
        f = ChoiceFilter(choices=[('a', 'a')], null_value='NULL', null_label='')
        self.assertEqual(f.field.choices, [
            ('', '---------'),
            ('NULL', ''),
            ('a', 'a'),
        ])

        # explicitly disable
        f = ChoiceFilter(choices=[('a', 'a')], null_label=None)
        self.assertEqual(f.field.choices, [
            ('', '---------'),
            ('a', 'a'),
        ])

    @override_settings(
        FILTERS_EMPTY_CHOICE_LABEL='EMPTY LABEL',
        FILTERS_NULL_CHOICE_LABEL='NULL LABEL',
        FILTERS_NULL_CHOICE_VALUE='NULL VALUE', )
    def test_settings_overrides(self):
        f = ChoiceFilter(choices=[('a', 'a')], )
        self.assertEqual(f.field.choices, [
            ('', 'EMPTY LABEL'),
            ('NULL VALUE', 'NULL LABEL'),
            ('a', 'a'),
        ])

    def test_callable_choices(self):
        def choices():
            yield ('a', 'a')
            yield ('b', 'b')

        f = ChoiceFilter(choices=choices)
        self.assertEqual(f.field.choices, [
            ('', '---------'),
            ('a', 'a'),
            ('b', 'b'),
        ])


class MultipleChoiceFilterTests(TestCase):

    def test_default_field(self):
        f = MultipleChoiceFilter()
        field = f.field
        self.assertIsInstance(field, forms.MultipleChoiceField)

    def test_filtering_requires_name(self):
        qs = mock.Mock(spec=['filter'])
        f = MultipleChoiceFilter()
        with self.assertRaises(TypeError):
            f.filter(qs, ['value'])

    def test_conjoined_default_value(self):
        f = MultipleChoiceFilter()
        self.assertFalse(f.conjoined)

    def test_conjoined_true(self):
        f = MultipleChoiceFilter(conjoined=True)
        self.assertTrue(f.conjoined)

    def test_filtering(self):
        qs = mock.Mock(spec=['filter'])
        f = MultipleChoiceFilter(name='somefield')
        with mock.patch('django_filters.filters.Q') as mockQclass:
            mockQ1, mockQ2 = mock.MagicMock(), mock.MagicMock()
            mockQclass.side_effect = [mockQ1, mockQ2]

            f.filter(qs, ['value'])

            self.assertEqual(mockQclass.call_args_list,
                             [mock.call(), mock.call(somefield='value')])
            mockQ1.__ior__.assert_called_once_with(mockQ2)
            qs.filter.assert_called_once_with(mockQ1.__ior__.return_value)
            qs.filter.return_value.distinct.assert_called_once_with()

    def test_filtering_exclude(self):
        qs = mock.Mock(spec=['exclude'])
        f = MultipleChoiceFilter(name='somefield', exclude=True)
        with mock.patch('django_filters.filters.Q') as mockQclass:
            mockQ1, mockQ2 = mock.MagicMock(), mock.MagicMock()
            mockQclass.side_effect = [mockQ1, mockQ2]

            f.filter(qs, ['value'])

            self.assertEqual(mockQclass.call_args_list,
                             [mock.call(), mock.call(somefield='value')])
            mockQ1.__ior__.assert_called_once_with(mockQ2)
            qs.exclude.assert_called_once_with(mockQ1.__ior__.return_value)
            qs.exclude.return_value.distinct.assert_called_once_with()

    def test_filtering_on_required_skipped_when_len_of_value_is_len_of_field_choices(self):
        qs = mock.Mock(spec=[])
        f = MultipleChoiceFilter(name='somefield', required=True)
        f.always_filter = False
        result = f.filter(qs, [])
        self.assertEqual(len(f.field.choices), 0)
        self.assertEqual(qs, result)

        f.field.choices = ['some', 'values', 'here']
        result = f.filter(qs, ['some', 'values', 'here'])
        self.assertEqual(qs, result)

        result = f.filter(qs, ['other', 'values', 'there'])
        self.assertEqual(qs, result)

    def test_filtering_skipped_with_empty_list_value_and_some_choices(self):
        qs = mock.Mock(spec=[])
        f = MultipleChoiceFilter(name='somefield')
        f.field.choices = ['some', 'values', 'here']
        result = f.filter(qs, [])
        self.assertEqual(qs, result)

    def test_filter_conjoined_true(self):
        """Tests that a filter with `conjoined=True` returns objects that
        have all the values included in `value`. For example filter
        users that have all of this books.

        """
        book_kwargs = {'price': 1, 'average_rating': 1}
        books = []
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))

        user1 = User.objects.create()
        user2 = User.objects.create()
        user3 = User.objects.create()
        user4 = User.objects.create()
        user5 = User.objects.create()

        user1.favorite_books.add(books[0], books[1])
        user2.favorite_books.add(books[0], books[1], books[2])
        user3.favorite_books.add(books[1], books[2])
        user4.favorite_books.add(books[2], books[3])
        user5.favorite_books.add(books[4], books[5])

        filter_list = (
            ((books[0].pk, books[0].pk),  # values
             [1, 2]),  # list of user.pk that have `value` books
            ((books[1].pk, books[1].pk),
             [1, 2, 3]),
            ((books[2].pk, books[2].pk),
             [2, 3, 4]),
            ((books[3].pk, books[3].pk),
             [4, ]),
            ((books[4].pk, books[4].pk),
             [5, ]),
            ((books[0].pk, books[1].pk),
             [1, 2]),
            ((books[0].pk, books[2].pk),
             [2, ]),
            ((books[1].pk, books[2].pk),
             [2, 3]),
            ((books[2].pk, books[3].pk),
             [4, ]),
            ((books[4].pk, books[5].pk),
             [5, ]),
            ((books[3].pk, books[4].pk),
             []),
        )
        users = User.objects.all()

        for item in filter_list:
            f = MultipleChoiceFilter(name='favorite_books__pk', conjoined=True)
            queryset = f.filter(users, item[0])
            expected_pks = [c[0] for c in queryset.values_list('pk')]
            self.assertListEqual(
                expected_pks,
                item[1],
                'Lists Differ: {0} != {1} for case {2}'.format(
                    expected_pks, item[1], item[0]))


class TypedMultipleChoiceFilterTests(TestCase):

    def test_default_field(self):
        f = TypedMultipleChoiceFilter()
        field = f.field
        self.assertIsInstance(field, forms.TypedMultipleChoiceField)

    def test_filtering_requires_name(self):
        qs = mock.Mock(spec=['filter'])
        f = TypedMultipleChoiceFilter()
        with self.assertRaises(TypeError):
            f.filter(qs, ['value'])

    def test_conjoined_default_value(self):
        f = TypedMultipleChoiceFilter()
        self.assertFalse(f.conjoined)

    def test_conjoined_true(self):
        f = TypedMultipleChoiceFilter(conjoined=True)
        self.assertTrue(f.conjoined)

    def test_filtering(self):
        qs = mock.Mock(spec=['filter'])
        f = TypedMultipleChoiceFilter(name='somefield')
        with mock.patch('django_filters.filters.Q') as mockQclass:
            mockQ1, mockQ2 = mock.MagicMock(), mock.MagicMock()
            mockQclass.side_effect = [mockQ1, mockQ2]

            f.filter(qs, ['value'])

            self.assertEqual(mockQclass.call_args_list,
                             [mock.call(), mock.call(somefield='value')])
            mockQ1.__ior__.assert_called_once_with(mockQ2)
            qs.filter.assert_called_once_with(mockQ1.__ior__.return_value)
            qs.filter.return_value.distinct.assert_called_once_with()

    def test_filtering_exclude(self):
        qs = mock.Mock(spec=['exclude'])
        f = TypedMultipleChoiceFilter(name='somefield', exclude=True)
        with mock.patch('django_filters.filters.Q') as mockQclass:
            mockQ1, mockQ2 = mock.MagicMock(), mock.MagicMock()
            mockQclass.side_effect = [mockQ1, mockQ2]

            f.filter(qs, ['value'])

            self.assertEqual(mockQclass.call_args_list,
                             [mock.call(), mock.call(somefield='value')])
            mockQ1.__ior__.assert_called_once_with(mockQ2)
            qs.exclude.assert_called_once_with(mockQ1.__ior__.return_value)
            qs.exclude.return_value.distinct.assert_called_once_with()

    def test_filtering_on_required_skipped_when_len_of_value_is_len_of_field_choices(self):
        qs = mock.Mock(spec=[])
        f = TypedMultipleChoiceFilter(name='somefield', required=True)
        f.always_filter = False
        result = f.filter(qs, [])
        self.assertEqual(len(f.field.choices), 0)
        self.assertEqual(qs, result)

        f.field.choices = ['some', 'values', 'here']
        result = f.filter(qs, ['some', 'values', 'here'])
        self.assertEqual(qs, result)

        result = f.filter(qs, ['other', 'values', 'there'])
        self.assertEqual(qs, result)

    def test_filtering_skipped_with_empty_list_value_and_some_choices(self):
        qs = mock.Mock(spec=[])
        f = TypedMultipleChoiceFilter(name='somefield')
        f.field.choices = ['some', 'values', 'here']
        result = f.filter(qs, [])
        self.assertEqual(qs, result)

    def test_filter_conjoined_true(self):
        """Tests that a filter with `conjoined=True` returns objects that
        have all the values included in `value`. For example filter
        users that have all of this books.

        """
        book_kwargs = {'price': 1, 'average_rating': 1}
        books = []
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))
        books.append(Book.objects.create(**book_kwargs))

        user1 = User.objects.create()
        user2 = User.objects.create()
        user3 = User.objects.create()
        user4 = User.objects.create()
        user5 = User.objects.create()

        user1.favorite_books.add(books[0], books[1])
        user2.favorite_books.add(books[0], books[1], books[2])
        user3.favorite_books.add(books[1], books[2])
        user4.favorite_books.add(books[2], books[3])
        user5.favorite_books.add(books[4], books[5])

        filter_list = (
            ((books[0].pk, books[0].pk),  # values
             [1, 2]),  # list of user.pk that have `value` books
            ((books[1].pk, books[1].pk),
             [1, 2, 3]),
            ((books[2].pk, books[2].pk),
             [2, 3, 4]),
            ((books[3].pk, books[3].pk),
             [4, ]),
            ((books[4].pk, books[4].pk),
             [5, ]),
            ((books[0].pk, books[1].pk),
             [1, 2]),
            ((books[0].pk, books[2].pk),
             [2, ]),
            ((books[1].pk, books[2].pk),
             [2, 3]),
            ((books[2].pk, books[3].pk),
             [4, ]),
            ((books[4].pk, books[5].pk),
             [5, ]),
            ((books[3].pk, books[4].pk),
             []),
        )
        users = User.objects.all()

        for item in filter_list:
            f = TypedMultipleChoiceFilter(name='favorite_books__pk', conjoined=True)
            queryset = f.filter(users, item[0])
            expected_pks = [c[0] for c in queryset.values_list('pk')]
            self.assertListEqual(
                expected_pks,
                item[1],
                'Lists Differ: {0} != {1} for case {2}'.format(
                    expected_pks, item[1], item[0]))


class DateFilterTests(TestCase):

    def test_default_field(self):
        f = DateFilter()
        field = f.field
        self.assertIsInstance(field, forms.DateField)


class DateTimeFilterTests(TestCase):

    def test_default_field(self):
        f = DateTimeFilter()
        field = f.field
        self.assertIsInstance(field, forms.DateTimeField)


class TimeFilterTests(TestCase):

    def test_default_field(self):
        f = TimeFilter()
        field = f.field
        self.assertIsInstance(field, forms.TimeField)


class DurationFilterTests(TestCase):

    def test_default_field(self):
        f = DurationFilter()
        field = f.field
        self.assertIsInstance(field, forms.DurationField)


class ModelChoiceFilterTests(TestCase):

    def test_default_field_without_queryset(self):
        f = ModelChoiceFilter()
        with self.assertRaises(TypeError):
            f.field

    def test_default_field_with_queryset(self):
        qs = mock.NonCallableMock(spec=[])
        f = ModelChoiceFilter(queryset=qs)
        field = f.field
        self.assertIsInstance(field, forms.ModelChoiceField)
        self.assertEqual(field.queryset, qs)

    def test_callable_queryset(self):
        request = mock.NonCallableMock(spec=[])
        qs = mock.NonCallableMock(spec=[])

        qs_callable = mock.Mock(return_value=qs)

        f = ModelChoiceFilter(queryset=qs_callable)
        f.parent = mock.Mock(request=request)
        field = f.field

        qs_callable.assert_called_with(request)
        self.assertEqual(field.queryset, qs)

    def test_get_queryset_override(self):
        request = mock.NonCallableMock(spec=[])
        qs = mock.NonCallableMock(spec=[])

        class F(ModelChoiceFilter):
            get_queryset = mock.create_autospec(ModelChoiceFilter.get_queryset, return_value=qs)

        f = F()
        f.parent = mock.Mock(request=request)
        field = f.field

        f.get_queryset.assert_called_with(f, request)
        self.assertEqual(field.queryset, qs)


class ModelMultipleChoiceFilterTests(TestCase):

    def test_default_field_without_queryset(self):
        f = ModelMultipleChoiceFilter()
        with self.assertRaises(TypeError):
            f.field

    def test_default_field_with_queryset(self):
        qs = mock.NonCallableMock(spec=[])
        f = ModelMultipleChoiceFilter(queryset=qs)
        field = f.field
        self.assertIsInstance(field, forms.ModelMultipleChoiceField)
        self.assertEqual(field.queryset, qs)

    def test_filtering_to_field_name(self):
        qs = User.objects.all()
        f = ModelMultipleChoiceFilter(name='first_name',
                                      to_field_name='first_name',
                                      queryset=qs)
        user = User.objects.create(first_name='Firstname')

        self.assertEqual(f.get_filter_predicate(user),
                         {'first_name': 'Firstname'})
        self.assertEqual(f.get_filter_predicate('FilterValue'),
                         {'first_name': 'FilterValue'})

        self.assertEqual(list(f.filter(qs, ['Firstname'])), [user])
        self.assertEqual(list(f.filter(qs, [user])), [user])

    def test_callable_queryset(self):
        request = mock.NonCallableMock(spec=[])
        qs = mock.NonCallableMock(spec=[])

        qs_callable = mock.Mock(return_value=qs)

        f = ModelMultipleChoiceFilter(queryset=qs_callable)
        f.parent = mock.Mock(request=request)
        field = f.field

        qs_callable.assert_called_with(request)
        self.assertEqual(field.queryset, qs)


class NumberFilterTests(TestCase):

    def test_default_field(self):
        f = NumberFilter()
        field = f.field
        self.assertIsInstance(field, forms.DecimalField)

    def test_filtering(self):
        qs = mock.Mock(spec=['filter'])
        f = NumberFilter()
        f.filter(qs, 1)
        qs.filter.assert_called_once_with(None__exact=1)
        # Also test 0 as it once had a bug
        qs.reset_mock()
        f.filter(qs, 0)
        qs.filter.assert_called_once_with(None__exact=0)

    def test_filtering_exclude(self):
        qs = mock.Mock(spec=['exclude'])
        f = NumberFilter(exclude=True)
        f.filter(qs, 1)
        qs.exclude.assert_called_once_with(None__exact=1)
        # Also test 0 as it once had a bug
        qs.reset_mock()
        f.filter(qs, 0)
        qs.exclude.assert_called_once_with(None__exact=0)


class NumericRangeFilterTests(TestCase):

    def test_default_field(self):
        f = NumericRangeFilter()
        field = f.field
        self.assertIsInstance(field, RangeField)

    def test_filtering(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=20, stop=30)
        f = NumericRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__exact=(20, 30))

    def test_filtering_exclude(self):
        qs = mock.Mock(spec=['exclude'])
        value = mock.Mock(start=20, stop=30)
        f = NumericRangeFilter(exclude=True)
        f.filter(qs, value)
        qs.exclude.assert_called_once_with(None__exact=(20, 30))

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock(spec=['filter'])
        f = NumericRangeFilter()
        result = f.filter(qs, None)
        self.assertEqual(qs, result)

    def test_field_with_lookup_expr(self):
        qs = mock.Mock()
        value = mock.Mock(start=20, stop=30)
        f = NumericRangeFilter(lookup_expr=('overlap'))
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__overlap=(20, 30))

    def test_zero_to_zero(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=0, stop=0)
        f = NumericRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__exact=(0, 0))

    def test_filtering_startswith(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=20, stop=None)
        f = NumericRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__startswith=20)

    def test_filtering_endswith(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=None, stop=30)
        f = NumericRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__endswith=30)


class RangeFilterTests(TestCase):

    def test_default_field(self):
        f = RangeFilter()
        field = f.field
        self.assertIsInstance(field, RangeField)

    def test_filtering_range(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=20, stop=30)
        f = RangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__range=(20, 30))

    def test_filtering_exclude(self):
        qs = mock.Mock(spec=['exclude'])
        value = mock.Mock(start=20, stop=30)
        f = RangeFilter(exclude=True)
        f.filter(qs, value)
        qs.exclude.assert_called_once_with(None__range=(20, 30))

    def test_filtering_start(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=20, stop=None)
        f = RangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__gte=20)

    def test_filtering_stop(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=None, stop=30)
        f = RangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__lte=30)

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock(spec=['filter'])
        f = RangeFilter()
        result = f.filter(qs, None)
        self.assertEqual(qs, result)

    def test_filtering_ignores_lookup_expr(self):
        qs = mock.Mock()
        value = mock.Mock(start=20, stop=30)
        f = RangeFilter(lookup_expr='gte')
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__range=(20, 30))


class DateRangeFilterTests(TestCase):

    def test_creating(self):
        f = DateRangeFilter()
        self.assertIn('choices', f.extra)
        self.assertEqual(len(DateRangeFilter.options), len(f.extra['choices']))

    def test_default_field(self):
        f = DateRangeFilter()
        field = f.field
        self.assertIsInstance(field, forms.ChoiceField)

    def test_filtering(self):
        # skip filtering, as it's an empty value
        qs = mock.Mock(spec=[])
        f = DateRangeFilter()
        result = f.filter(qs, '')
        self.assertEqual(qs, result)

    def test_filtering_skipped_with_out_of_range_value(self):
        # Field validation should prevent this from occuring
        qs = mock.Mock(spec=[])
        f = DateRangeFilter()
        with self.assertRaises(AssertionError):
            f.filter(qs, 999)

    def test_filtering_for_this_year(self):
        qs = mock.Mock(spec=['filter'])
        with mock.patch('django_filters.filters.now') as mock_now:
            now_dt = mock_now.return_value
            f = DateRangeFilter()
            f.filter(qs, '4')
            qs.filter.assert_called_once_with(
                None__year=now_dt.year)

    def test_filtering_for_this_month(self):
        qs = mock.Mock(spec=['filter'])
        with mock.patch('django_filters.filters.now') as mock_now:
            now_dt = mock_now.return_value
            f = DateRangeFilter()
            f.filter(qs, '3')
            qs.filter.assert_called_once_with(
                None__year=now_dt.year, None__month=now_dt.month)

    def test_filtering_for_7_days(self):
        qs = mock.Mock(spec=['filter'])
        with mock.patch('django_filters.filters.now'), \
                mock.patch('django_filters.filters.timedelta') as mock_td, \
                mock.patch('django_filters.filters._truncate') as mock_truncate:
            mock_d1, mock_d2 = mock.MagicMock(), mock.MagicMock()
            mock_truncate.side_effect = [mock_d1, mock_d2]
            f = DateRangeFilter()
            f.filter(qs, '2')
            self.assertEqual(
                mock_td.call_args_list,
                [mock.call(days=7), mock.call(days=1)]
            )
            qs.filter.assert_called_once_with(None__lt=mock_d2, None__gte=mock_d1)

    def test_filtering_for_today(self):
        qs = mock.Mock(spec=['filter'])
        with mock.patch('django_filters.filters.now') as mock_now:
            now_dt = mock_now.return_value
            f = DateRangeFilter()
            f.filter(qs, '1')
            qs.filter.assert_called_once_with(
                None__year=now_dt.year,
                None__month=now_dt.month,
                None__day=now_dt.day)

    def test_filtering_for_yesterday(self):
        qs = mock.Mock(spec=['filter'])
        with mock.patch('django_filters.filters.now') as mock_now:
            now_dt = mock_now.return_value
            f = DateRangeFilter()
            f.filter(qs, '5')
            qs.filter.assert_called_once_with(
                None__year=now_dt.year,
                None__month=now_dt.month,
                None__day=(now_dt - timedelta(days=1)).day,
            )


class DateFromToRangeFilterTests(TestCase):

    def test_default_field(self):
        f = DateFromToRangeFilter()
        field = f.field
        self.assertIsInstance(field, DateRangeField)

    def test_filtering_range(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=date(2015, 4, 7), stop=date(2015, 9, 6))
        f = DateFromToRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(
            None__range=(date(2015, 4, 7), date(2015, 9, 6)))

    def test_filtering_start(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=date(2015, 4, 7), stop=None)
        f = DateFromToRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__gte=date(2015, 4, 7))

    def test_filtering_stop(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=None, stop=date(2015, 9, 6))
        f = DateFromToRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__lte=date(2015, 9, 6))

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock(spec=['filter'])
        f = DateFromToRangeFilter()
        result = f.filter(qs, None)
        self.assertEqual(qs, result)

    def test_filtering_ignores_lookup_expr(self):
        qs = mock.Mock()
        value = mock.Mock(start=date(2015, 4, 7), stop=date(2015, 9, 6))
        f = DateFromToRangeFilter(lookup_expr='gte')
        f.filter(qs, value)
        qs.filter.assert_called_once_with(
            None__range=(date(2015, 4, 7), date(2015, 9, 6)))


class DateTimeFromToRangeFilterTests(TestCase):

    def test_default_field(self):
        f = DateTimeFromToRangeFilter()
        field = f.field
        self.assertIsInstance(field, DateTimeRangeField)

    def test_filtering_range(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(
            start=datetime(2015, 4, 7, 8, 30), stop=datetime(2015, 9, 6, 11, 45))
        f = DateTimeFromToRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(
            None__range=(datetime(2015, 4, 7, 8, 30), datetime(2015, 9, 6, 11, 45)))

    def test_filtering_start(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=datetime(2015, 4, 7, 8, 30), stop=None)
        f = DateTimeFromToRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__gte=datetime(2015, 4, 7, 8, 30))

    def test_filtering_stop(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=None, stop=datetime(2015, 9, 6, 11, 45))
        f = DateTimeFromToRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__lte=datetime(2015, 9, 6, 11, 45))

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock(spec=['filter'])
        f = DateTimeFromToRangeFilter()
        result = f.filter(qs, None)
        self.assertEqual(qs, result)

    def test_filtering_ignores_lookup_expr(self):
        qs = mock.Mock()
        value = mock.Mock(
            start=datetime(2015, 4, 7, 8, 30), stop=datetime(2015, 9, 6, 11, 45))
        f = DateTimeFromToRangeFilter(lookup_expr='gte')
        f.filter(qs, value)
        qs.filter.assert_called_once_with(
            None__range=(datetime(2015, 4, 7, 8, 30), datetime(2015, 9, 6, 11, 45)))


class TimeRangeFilterTests(TestCase):

    def test_default_field(self):
        f = TimeRangeFilter()
        field = f.field
        self.assertIsInstance(field, TimeRangeField)

    def test_filtering_range(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=time(10, 15), stop=time(12, 30))
        f = TimeRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(
            None__range=(time(10, 15), time(12, 30)))

    def test_filtering_start(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=time(10, 15), stop=None)
        f = TimeRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__gte=time(10, 15))

    def test_filtering_stop(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=None, stop=time(12, 30))
        f = TimeRangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__lte=time(12, 30))

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock(spec=['filter'])
        f = TimeRangeFilter()
        result = f.filter(qs, None)
        self.assertEqual(qs, result)

    def test_filtering_ignores_lookup_expr(self):
        qs = mock.Mock()
        value = mock.Mock(start=time(10, 15), stop=time(12, 30))
        f = TimeRangeFilter(lookup_expr='gte')
        f.filter(qs, value)
        qs.filter.assert_called_once_with(
            None__range=(time(10, 15), time(12, 30)))


class AllValuesFilterTests(TestCase):

    def test_default_field_without_assigning_model(self):
        f = AllValuesFilter()
        with self.assertRaises(AttributeError):
            f.field

    def test_default_field_with_assigning_model(self):
        mocked = mock.Mock()
        chained_call = '.'.join(['_default_manager', 'distinct.return_value',
                                 'order_by.return_value',
                                 'values_list.return_value'])
        mocked.configure_mock(**{chained_call: iter([])})
        f = AllValuesFilter()
        f.model = mocked
        field = f.field
        self.assertIsInstance(field, forms.ChoiceField)


class LookupTypesTests(TestCase):
    def test_custom_lookup_exprs(self):
        filters.LOOKUP_TYPES = [
            ('', '---------'),
            ('exact', 'Is equal to'),
            ('not_exact', 'Is not equal to'),
            ('lt', 'Lesser than'),
            ('gt', 'Greater than'),
            ('gte', 'Greater than or equal to'),
            ('lte', 'Lesser than or equal to'),
            ('startswith', 'Starts with'),
            ('endswith', 'Ends with'),
            ('contains', 'Contains'),
            ('not_contains', 'Does not contain'),
        ]

        f = Filter(lookup_expr=None)
        field = f.field
        choice_field = field.fields[1]
        all_choices = choice_field.choices

        self.assertIsInstance(field, LookupTypeField)
        self.assertEqual(all_choices, filters.LOOKUP_TYPES)
        self.assertEqual(all_choices[1][0], 'exact')
        self.assertEqual(all_choices[1][1], 'Is equal to')

        custom_f = Filter(lookup_expr=('endswith', 'not_contains'))
        custom_field = custom_f.field
        custom_choice_field = custom_field.fields[1]
        my_custom_choices = custom_choice_field.choices

        available_lookup_exprs = [
            ('endswith', 'Ends with'),
            ('not_contains', 'Does not contain'),
        ]

        self.assertIsInstance(custom_field, LookupTypeField)
        self.assertEqual(my_custom_choices, available_lookup_exprs)
        self.assertEqual(my_custom_choices[0][0], 'endswith')
        self.assertEqual(my_custom_choices[0][1], 'Ends with')
        self.assertEqual(my_custom_choices[1][0], 'not_contains')
        self.assertEqual(my_custom_choices[1][1], 'Does not contain')


class CSVFilterTests(TestCase):
    def setUp(self):
        class NumberInFilter(BaseCSVFilter, NumberFilter):
            pass

        class DateTimeYearInFilter(BaseCSVFilter, DateTimeFilter):
            pass

        self.number_in = NumberInFilter(lookup_expr='in')
        self.datetimeyear_in = DateTimeYearInFilter(lookup_expr='year__in')

    def test_default_field(self):
        f = BaseCSVFilter()
        field = f.field
        self.assertIsInstance(field, forms.Field)

    def test_concrete_field(self):
        field = self.number_in.field
        self.assertIsInstance(field, forms.DecimalField)
        self.assertIsInstance(field, BaseCSVField)
        self.assertEqual(field.__class__.__name__, 'DecimalInField')

        field = self.datetimeyear_in.field
        self.assertIsInstance(field, forms.DateTimeField)
        self.assertIsInstance(field, BaseCSVField)
        self.assertEqual(field.__class__.__name__, 'DateTimeYearInField')

    def test_filtering(self):
        qs = mock.Mock(spec=['filter'])
        f = self.number_in
        f.filter(qs, [1, 2])
        qs.filter.assert_called_once_with(None__in=[1, 2])

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock(spec=['filter'])
        f = self.number_in
        result = f.filter(qs, None)
        self.assertEqual(qs, result)

    def test_field_with_lookup_expr(self):
        qs = mock.Mock()
        f = self.datetimeyear_in
        f.filter(qs, [1, 2])
        qs.filter.assert_called_once_with(None__year__in=[1, 2])


class BaseInFilterTests(TestCase):
    def test_filtering(self):
        class NumberInFilter(BaseInFilter, NumberFilter):
            pass

        qs = mock.Mock(spec=['filter'])
        f = NumberInFilter()
        f.filter(qs, [1, 2])
        qs.filter.assert_called_once_with(None__in=[1, 2])


class BaseRangeFilterTests(TestCase):
    def test_filtering(self):
        class NumberInFilter(BaseRangeFilter, NumberFilter):
            pass

        qs = mock.Mock(spec=['filter'])
        f = NumberInFilter()
        f.filter(qs, [1, 2])
        qs.filter.assert_called_once_with(None__range=[1, 2])


class OrderingFilterTests(TestCase):
    def test_default_field(self):
        f = OrderingFilter()
        field = f.field
        self.assertIsInstance(field, forms.ChoiceField)

    def test_filtering(self):
        qs = mock.Mock(spec=['order_by'])
        f = OrderingFilter()
        f.filter(qs, ['a', 'b'])
        qs.order_by.assert_called_once_with('a', 'b')

    def test_filtering_descending(self):
        qs = mock.Mock(spec=['order_by'])
        f = OrderingFilter()
        f.filter(qs, ['-a'])
        qs.order_by.assert_called_once_with('-a')

    def test_filtering_with_fields(self):
        qs = mock.Mock(spec=['order_by'])
        f = OrderingFilter(fields={'a': 'b'})
        f.filter(qs, ['b', '-b'])
        qs.order_by.assert_called_once_with('a', '-a')

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock(spec=['order_by'])
        f = OrderingFilter()
        result = f.filter(qs, None)
        self.assertEqual(qs, result)

    def test_choices_unaltered(self):
        # provided 'choices' should not be altered when 'fields' is present
        f = OrderingFilter(
            choices=(('a', 'A'), ('b', 'B')),
            fields=(('a', 'c'), ('b', 'd')),
        )

        self.assertSequenceEqual(f.field.choices, (
            ('', '---------'),
            ('a', 'A'),
            ('b', 'B'),
        ))

    def test_choices_from_fields(self):
        f = OrderingFilter(
            fields=(('a', 'c'), ('b', 'd')),
        )

        self.assertSequenceEqual(f.field.choices, (
            ('', '---------'),
            ('c', 'C'),
            ('-c', 'C (descending)'),
            ('d', 'D'),
            ('-d', 'D (descending)'),
        ))

    def test_field_labels(self):
        f = OrderingFilter(
            fields=(('a', 'c'), ('b', 'd')),
            field_labels={'a': 'foo'},
        )

        self.assertSequenceEqual(f.field.choices, (
            ('', '---------'),
            ('c', 'foo'),
            ('-c', 'foo (descending)'),
            ('d', 'D'),
            ('-d', 'D (descending)'),
        ))

    def test_field_labels_descending(self):
        f = OrderingFilter(
            fields=['username'],
            field_labels={
                'username': 'BLABLA',
                '-username': 'XYZXYZ',
            }
        )

        self.assertEqual(f.field.choices, [
            ('', '---------'),
            ('username', 'BLABLA'),
            ('-username', 'XYZXYZ'),
        ])

    def test_normalize_fields(self):
        f = OrderingFilter.normalize_fields
        O = OrderedDict

        self.assertIn('a', f({'a': 'b'}))

        self.assertEqual(
            f(O([('a', 'b'), ('c', 'd')])),
            O([('a', 'b'), ('c', 'd')])
        )

        self.assertEqual(
            f([('a', 'b'), ('c', 'd')]),
            O([('a', 'b'), ('c', 'd')])
        )

        self.assertEqual(
            f(['a', 'b']),
            O([('a', 'a'), ('b', 'b')])
        )

        with self.assertRaises(AssertionError) as ctx:
            f(None)
        self.assertEqual(str(ctx.exception), "'fields' must be an iterable (e.g., a list, tuple, or mapping).")

        with self.assertRaises(AssertionError) as ctx:
            f([('a', 'b', 'c')])
        self.assertEqual(str(ctx.exception), "'fields' must contain strings or (field name, param name) pairs.")

        with self.assertRaises(AssertionError) as ctx:
            f([0, 1, 2])
        self.assertEqual(str(ctx.exception), "'fields' must contain strings or (field name, param name) pairs.")

    def test_widget(self):
        f = OrderingFilter()
        widget = f.field.widget

        self.assertIsInstance(widget, widgets.BaseCSVWidget)
        self.assertIsInstance(widget, forms.Select)

    def test_translation_sanity(self):
        with translation.override('pl'):
            self.assertEqual(_('Username'), 'Nazwa użytkownika')
            self.assertEqual(_('%s (descending)') % _('Username'), 'Nazwa użytkownika (malejąco)')

    def test_translation_default_label(self):
        with translation.override('pl'):
            f = OrderingFilter(fields=['username'])

            self.assertEqual(f.field.choices, [
                ('', '---------'),
                ('username', 'Nazwa użytkownika'),
                ('-username', 'Nazwa użytkownika (malejąco)'),
            ])

    def test_translation_override_label(self):
        with translation.override('pl'):
            f = OrderingFilter(
                fields=['username'],
                field_labels={'username': 'BLABLA'},
            )

            self.assertEqual(f.field.choices, [
                ('', '---------'),
                ('username', 'BLABLA'),
                ('-username', 'BLABLA (malejąco)'),
            ])

    def test_help_text(self):
        # regression test for #756 - the ususal CSV help_text is not relevant to ordering filters.
        self.assertEqual(OrderingFilter().field.help_text, '')
        self.assertEqual(OrderingFilter(help_text='a').field.help_text, 'a')
