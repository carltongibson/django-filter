from __future__ import absolute_import
from __future__ import unicode_literals

import mock
import sys

if sys.version_info >= (2, 7):
    import unittest
else:  # pragma: nocover
    from django.utils import unittest  # noqa

from datetime import timedelta

from django import forms
from django.test import TestCase

from django_filters.fields import Lookup
from django_filters.fields import RangeField
from django_filters.fields import LookupTypeField
from django_filters.filters import Filter
from django_filters.filters import CharFilter
from django_filters.filters import BooleanFilter
from django_filters.filters import ChoiceFilter
from django_filters.filters import MultipleChoiceFilter
from django_filters.filters import DateFilter
from django_filters.filters import DateTimeFilter
from django_filters.filters import TimeFilter
from django_filters.filters import ModelChoiceFilter
from django_filters.filters import ModelMultipleChoiceFilter
from django_filters.filters import NumberFilter
from django_filters.filters import RangeFilter
from django_filters.filters import DateRangeFilter
from django_filters.filters import AllValuesFilter
from django_filters.filters import LOOKUP_TYPES

from tests.models import Book, User


class FilterTests(TestCase):

    def test_creation(self):
        f = Filter()
        self.assertEqual(f.lookup_type, 'exact')
        self.assertEqual(f.exclude, False)

    def test_creation_order(self):
        f = Filter()
        f2 = Filter()
        self.assertTrue(f2.creation_counter > f.creation_counter)

    def test_default_field(self):
        f = Filter()
        field = f.field
        self.assertIsInstance(field, forms.Field)
        self.assertEqual(field.help_text, '')

    def test_field_with_exclusion(self):
        f = Filter(exclude=True)
        field = f.field
        self.assertIsInstance(field, forms.Field)
        self.assertEqual(field.help_text, 'This is an exclusion filter')

    def test_field_with_single_lookup_type(self):
        f = Filter(lookup_type='iexact')
        field = f.field
        self.assertIsInstance(field, forms.Field)

    def test_field_with_none_lookup_type(self):
        f = Filter(lookup_type=None)
        field = f.field
        self.assertIsInstance(field, LookupTypeField)
        choice_field = field.fields[1]
        self.assertEqual(len(choice_field.choices), len(LOOKUP_TYPES))

    def test_field_with_lookup_type_and_exlusion(self):
        f = Filter(lookup_type=None, exclude=True)
        field = f.field
        self.assertIsInstance(field, LookupTypeField)
        self.assertEqual(field.help_text, 'This is an exclusion filter')

    def test_field_with_list_lookup_type(self):
        f = Filter(lookup_type=('istartswith', 'iendswith'))
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
                label='somelabel', widget='somewidget', help_text=mock.ANY)

    def test_field_extra_params(self):
        with mock.patch.object(Filter, 'field_class',
                spec=['__call__']) as mocked:
            f = Filter(someattr='someattr')
            f.field
            mocked.assert_called_once_with(required=mock.ANY,
                label=mock.ANY, widget=mock.ANY, help_text=mock.ANY,
                someattr='someattr')

    def test_field_with_required_filter(self):
        with mock.patch.object(Filter, 'field_class',
                spec=['__call__']) as mocked:
            f = Filter(required=True)
            f.field
            mocked.assert_called_once_with(required=True,
                label=mock.ANY, widget=mock.ANY, help_text=mock.ANY)

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
        f = Filter(name='somefield', lookup_type=['some_lookup_type'])
        result = f.filter(qs, Lookup('value', 'some_lookup_type'))
        qs.filter.assert_called_once_with(somefield__some_lookup_type='value')
        self.assertNotEqual(qs, result)

    def test_filtering_skipped_with_list_value_with_blank(self):
        qs = mock.Mock()
        f = Filter(name='somefield', lookup_type=['some_lookup_type'])
        result = f.filter(qs, Lookup('', 'some_lookup_type'))
        self.assertListEqual(qs.method_calls, [])
        self.assertEqual(qs, result)

    def test_filtering_skipped_with_list_value_with_blank_lookup(self):
        return # Now field is required to provide valid lookup_type if it provides any
        qs = mock.Mock(spec=['filter'])
        f = Filter(name='somefield', lookup_type=None)
        result = f.filter(qs, Lookup('value', ''))
        qs.filter.assert_called_once_with(somefield__exact='value')
        self.assertNotEqual(qs, result)

    def test_filter_using_action(self):
        qs = mock.NonCallableMock(spec=[])
        action = mock.Mock(spec=['filter'])
        f = Filter(action=action)
        result = f.filter(qs, 'value')
        action.assert_called_once_with(qs, 'value')
        self.assertNotEqual(qs, result)

    def test_filtering_uses_distinct(self):
        qs = mock.Mock(spec=['filter', 'distinct'])
        f = Filter(name='somefield', distinct=True)
        f.filter(qs, 'value')
        result = qs.distinct.assert_called_once()
        self.assertNotEqual(qs, result)


class CharFilterTests(TestCase):

    def test_default_field(self):
        f = CharFilter()
        field = f.field
        self.assertIsInstance(field, forms.CharField)


class BooleanFilterTests(TestCase):

    def test_default_field(self):
        f = BooleanFilter()
        field = f.field
        self.assertIsInstance(field, forms.NullBooleanField)

    def test_filtering(self):
        qs = mock.Mock(spec=['filter'])
        f = BooleanFilter(name='somefield')
        result = f.filter(qs, True)
        qs.filter.assert_called_once_with(somefield=True)
        self.assertNotEqual(qs, result)

    @unittest.expectedFailure
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


class ChoiceFilterTests(TestCase):

    def test_default_field(self):
        f = ChoiceFilter()
        field = f.field
        self.assertIsInstance(field, forms.ChoiceField)


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

    @unittest.expectedFailure
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


class RangeFilterTests(TestCase):

    def test_default_field(self):
        f = RangeFilter()
        field = f.field
        self.assertIsInstance(field, RangeField)

    def test_filtering(self):
        qs = mock.Mock(spec=['filter'])
        value = mock.Mock(start=20, stop=30)
        f = RangeFilter()
        f.filter(qs, value)
        qs.filter.assert_called_once_with(None__range=(20, 30))

    def test_filtering_skipped_with_none_value(self):
        qs = mock.Mock(spec=['filter'])
        f = RangeFilter()
        result = f.filter(qs, None)
        self.assertEqual(qs, result)

    def test_filtering_ignores_lookup_type(self):
        qs = mock.Mock()
        value = mock.Mock(start=20, stop=30)
        f = RangeFilter(lookup_type='gte')
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
        qs = mock.Mock(spec=['all'])
        f = DateRangeFilter()
        f.filter(qs, '')
        qs.all.assert_called_once_with()

    # the correct behavior fails right now
    @unittest.expectedFailure
    def test_filtering_skipped_with_blank_value(self):
        qs = mock.Mock(spec=[])
        f = DateRangeFilter()
        result = f.filter(qs, '')
        self.assertEqual(qs, result)

    @unittest.expectedFailure
    def test_filtering_skipped_with_out_of_range_value(self):
        qs = mock.Mock(spec=[])
        f = DateRangeFilter()
        result = f.filter(qs, 999)
        self.assertEqual(qs, result)

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
        with mock.patch('django_filters.filters.now'):
            with mock.patch('django_filters.filters.timedelta') as mock_td:
                with mock.patch(
                        'django_filters.filters._truncate') as mock_truncate:
                    mock_dt1, mock_dt2 = mock.MagicMock(), mock.MagicMock()
                    mock_truncate.side_effect = [mock_dt1, mock_dt2]
                    f = DateRangeFilter()
                    f.filter(qs, '2')
                    self.assertEqual(mock_td.call_args_list,
                        [mock.call(days=7), mock.call(days=1)])
                    qs.filter.assert_called_once_with(
                        None__lt=mock_dt2, None__gte=mock_dt1)

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


class AllValuesFilterTests(TestCase):

    def test_default_field_without_assigning_model(self):
        f = AllValuesFilter()
        with self.assertRaises(AttributeError):
            f.field

    def test_default_field_with_assigning_model(self):
        mocked = mock.Mock()
        chained_call = '.'.join(['_default_manager', 'distinct.return_value',
            'order_by.return_value', 'values_list.return_value'])
        mocked.configure_mock(**{chained_call: iter([])})
        f = AllValuesFilter()
        f.model = mocked
        field = f.field
        self.assertIsInstance(field, forms.ChoiceField)
