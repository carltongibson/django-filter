import inspect
from unittest import mock

from django.db.models import Q
from django.test import TestCase

from django_filters import FilterSet, filters, groups
from django_filters.groups import BaseFilterGroup


class ModuleImportTests(TestCase):

    def test_imports(self):
        group_classes = [
            key for key, value
            in inspect.getmembers(groups)
            if isinstance(value, type) and issubclass(value, BaseFilterGroup)
        ]

        # sanity check
        self.assertIn('BaseFilterGroup', group_classes)
        self.assertIn('ExclusiveGroup', group_classes)

        # Ensure all group subclasses are included in groups.__all__
        self.assertSetEqual(set(group_classes), set(groups.__all__))


class FilterGroupInitTests(TestCase):

    def test_valid(self):
        group = BaseFilterGroup(['foo', 'bar'])
        self.assertEqual(group.filters, ['foo', 'bar'])

    def test_invalid_member_count(self):
        invalid = [
            ['foo'],
            [],
            None,
        ]

        msg = "A filter group must contain at least two members."
        for names in invalid:
            with self.subTest(filters=names):
                with self.assertRaisesMessage(ValueError, msg):
                    BaseFilterGroup(names)

    def test_duplicate_members(self):
        invalid = [
            ['foo', 'foo'],
            ['foo', 'bar', 'foo'],
        ]

        msg = "A filter group must not contain duplicate members."
        for names in invalid:
            with self.subTest(filters=names):
                with self.assertRaisesMessage(ValueError, msg):
                    BaseFilterGroup(names)


class FilterGroupExtractDataTests(TestCase):

    def test_original_data_unaltered(self):
        # The cleaned_data dict should be unaltered
        group = BaseFilterGroup(['foo', 'bar'])
        cleaned_data = {'foo': 1, 'bar': 2, 'baz': 3}

        # discard result - we're testing that input is unaltered
        group.extract_data(cleaned_data)
        self.assertEqual(cleaned_data, {'foo': 1, 'bar': 2, 'baz': 3})

    def test_combined_result_matches_original(self):
        group = BaseFilterGroup(['foo', 'bar'])
        cleaned_data = {'foo': 1, 'bar': 2, 'baz': 3}

        extract, rest = group.extract_data(cleaned_data)
        self.assertEqual({**extract, **rest}, {'foo': 1, 'bar': 2, 'baz': 3})

    def test_extract_not_in_rest(self):
        group = BaseFilterGroup(['foo', 'bar'])
        cleaned_data = {'foo': 1, 'bar': 2, 'baz': 3}

        extract, rest = group.extract_data(cleaned_data)
        self.assertEqual(set(extract) & set(rest), set())
        self.assertEqual(set(extract) ^ set(rest), set(cleaned_data))

    def test_missing_data(self):
        group = BaseFilterGroup(['foo', 'bar'])
        cleaned_data = {'foo': 1}

        extract, _ = group.extract_data(cleaned_data)
        self.assertEqual(extract, {'foo': 1})


class FilterGroupFormatLabelsTests(TestCase):

    def setUp(self):
        class F(FilterSet):
            foo = filters.CharFilter(label='who foo')
            bar = filters.CharFilter(label='What bar')
            baz = filters.CharFilter(label='When Baz')
            qux = filters.CharFilter(label='Where QUX')

        self.group = BaseFilterGroup(['foo', 'bar'])
        self.group.parent = F(data={}, queryset=mock.Mock())

    def test_format_labels(self):
        # (names, expected)
        cases = [
            (['foo'], "'who foo'"),
            (['foo', 'bar'], "'who foo' and 'What bar'"),
            (['bar', 'foo'], "'What bar' and 'who foo'"),
            (['foo', 'bar', 'baz'],
                "'who foo', 'What bar', and 'When Baz'"),
            (['foo', 'bar', 'baz', 'qux'],
                "'who foo', 'What bar', 'When Baz', and 'Where QUX'"),
        ]

        for names, expected in cases:
            with self.subTest(names=names):
                self.assertEqual(self.group.format_labels(names), expected)


class ConcreteFilterGroupSanityChecks:
    group_class = None

    class F(FilterSet):
        foo = filters.CharFilter(label='foo')
        bar = filters.CharFilter(label='bar')
        baz = filters.CharFilter(label='baz')

        ungrouped = filters.CharFilter(label='ungrouped')
        distinct = filters.CharFilter(label='distinct', distinct=True)
        negated = filters.CharFilter(label='negated', exclude=True)

    def setUp(self):
        self.group = self.group_class(['foo', 'bar', 'baz'])
        self.group.parent = self.F(data={}, queryset=mock.Mock())

    def test_validate_invalid_data(self):
        msg = "The `data` must be a subset of the group's `.filters`."
        with self.assertRaisesMessage(AssertionError, msg):
            self.group.validate(None, invalid='param')

        # 'ungrouped' filter not a member of the group
        with self.assertRaisesMessage(AssertionError, msg):
            self.group.validate(None, ungrouped='param')

    def test_filter_invalid_data(self):
        msg = "The `data` must be a subset of the group's `.filters`."
        with self.assertRaisesMessage(AssertionError, msg):
            self.group.filter(None, invalid='param')

        # 'ungrouped' filter not a member of the group
        with self.assertRaisesMessage(AssertionError, msg):
            self.group.filter(None, ungrouped='param')


class ExclusiveGroupTests(ConcreteFilterGroupSanityChecks, TestCase):
    group_class = groups.ExclusiveGroup

    def test_validation_error(self):
        form = mock.Mock()

        self.group.validate(form, foo='1', bar='2')

        # get ValidationError
        args, kwargs = form.add_error.call_args
        exc = args[1]
        msg = "'foo', 'bar', and 'baz' are mutually exclusive."

        self.assertEqual(exc.messages, [msg])

    def test_validate_none(self):
        form = mock.Mock()

        self.group.validate(form)

        form.add_error.assert_not_called()

    def test_validate_empty(self):
        form = mock.Mock()

        self.group.validate(form, foo='', bar='', baz='')

        form.add_error.assert_not_called()

    def test_validate_single(self):
        form = mock.Mock()

        self.group.validate(form, foo='1')
        self.group.validate(form, bar='1')

        form.add_error.assert_not_called()

    def test_validate_multiple_partial(self):
        # test if a partial set of filters are validated
        form = mock.Mock()

        self.group.validate(form, foo='1', bar='2')

        form.add_error.assert_has_calls([
            mock.call('foo', mock.ANY),
            mock.call('bar', mock.ANY),
        ], any_order=True)
        self.assertEqual(form.add_error.call_count, 2)

    def test_validate_multiple_all(self):
        # test if the entire set of filters are validated
        form = mock.Mock()

        # sanity check to ensure there are 3 members
        self.assertEqual(len(self.group.filters), 3)

        self.group.validate(form, foo='1', bar='2', baz='3')

        form.add_error.assert_has_calls([
            mock.call('foo', mock.ANY),
            mock.call('bar', mock.ANY),
            mock.call('baz', mock.ANY),
        ], any_order=True)
        self.assertEqual(form.add_error.call_count, 3)

    def test_filter_none(self):
        qs = mock.Mock()

        self.group.filter(qs)

        qs.filter.assert_not_called()

    def test_filter_single(self):
        qs = mock.Mock()

        self.group.filter(qs, foo='1')

        qs.filter.assert_called_once_with(foo__exact='1')

    def test_filter_multiple_partial(self):
        msg = "The `data` should consist of only one element."
        with self.assertRaisesMessage(AssertionError, msg):
            self.group.filter(None, foo='1', bar='2')

    def test_filter_multiple_all(self):
        msg = "The `data` should consist of only one element."
        with self.assertRaisesMessage(AssertionError, msg):
            self.group.filter(None, foo='1', bar='2', baz='3')


class RequiredGroupTests(ConcreteFilterGroupSanityChecks, TestCase):
    group_class = groups.RequiredGroup

    def test_validation_error(self):
        form = mock.Mock()

        self.group.validate(form, foo='1', bar='2')

        # get ValidationError
        args, kwargs = form.add_error.call_args
        exc = args[1]
        msg = "'foo', 'bar', and 'baz' are mutually required."

        self.assertEqual(exc.messages, [msg])

    def test_validate_none(self):
        form = mock.Mock()

        self.group.validate(form)

        form.add_error.assert_not_called()

    def test_validate_empty(self):
        form = mock.Mock()

        self.group.validate(form, foo='', bar='', baz='')

        form.add_error.assert_not_called()

    def test_validate_single(self):
        form = mock.Mock()

        self.group.validate(form, foo='1')

        form.add_error.assert_has_calls([
            mock.call('foo', mock.ANY),
            mock.call('bar', mock.ANY),
            mock.call('baz', mock.ANY),
        ], any_order=True)
        self.assertEqual(form.add_error.call_count, 3)

    def test_validate_multiple_partial(self):
        # test if a partial set of filters are validated
        form = mock.Mock()

        self.group.validate(form, foo='1', bar='2')

        form.add_error.assert_has_calls([
            mock.call('foo', mock.ANY),
            mock.call('bar', mock.ANY),
            mock.call('baz', mock.ANY),
        ], any_order=True)
        self.assertEqual(form.add_error.call_count, 3)

    def test_validate_multiple_all(self):
        # test if the entire set of filters are validated
        form = mock.Mock()

        # sanity check to ensure there are 3 members
        self.assertEqual(len(self.group.filters), 3)

        self.group.validate(form, foo='1', bar='2', baz='3')

        form.add_error.assert_not_called()

    def test_filter_none(self):
        qs = mock.Mock()

        self.group.filter(qs)

        qs.filter.assert_not_called()

    def test_filter_single(self):
        msg = "The `data` should contain all filters."
        with self.assertRaisesMessage(AssertionError, msg):
            self.group.filter(None, foo='1')

    def test_filter_multiple_partial(self):
        msg = "The `data` should contain all filters."
        with self.assertRaisesMessage(AssertionError, msg):
            self.group.filter(None, foo='1', bar='2')

    def test_filter_multiple_all(self):
        qs = mock.Mock()

        self.group.filter(qs, foo='1', bar='2', baz='3')

        # need to sort calls since call order not guaranteed
        self.assertEqual(sorted(qs.filter.mock_calls), [
            mock.call(foo__exact='1'),
            mock.call().filter(bar__exact='2'),
            mock.call().filter().filter(baz__exact='3'),
        ])


class CombinedGroupTests(ConcreteFilterGroupSanityChecks, TestCase):
    group_class = groups.CombinedGroup

    def test_filter_none(self):
        qs = mock.Mock()

        self.group.filter(qs)

        qs.filter.assert_not_called()

    def test_filter_single(self):
        qs = mock.Mock()

        self.group.filter(qs, foo='1')

        qs.filter.assert_called_once_with(Q(foo__exact='1'))

    def test_filter_multiple(self):
        qs = mock.Mock()

        self.group.filter(qs, foo='1', bar='2', baz='3')

        # Unpack Q object from filter call args
        args, _ = qs.filter.call_args
        q_obj, = args  # note that `,` unpacks the list

        self.assertEqual(q_obj.connector, 'AND')
        self.assertEqual(sorted(q_obj.children), [
            ('bar__exact', '2'),
            ('baz__exact', '3'),
            ('foo__exact', '1'),
        ])

    def test_filter_distinct(self):
        qs = mock.Mock()
        group = self.group_class(['foo', 'distinct'])
        group.parent = self.F(data={}, queryset=mock.Mock())

        group.filter(qs, foo='1', distinct='2')

        # Unpack Q object from filter call args
        args, _ = qs.filter.call_args
        q_obj, = args  # note that `,` unpacks the list

        # need to sort calls since call order not guaranteed
        self.assertEqual(q_obj.connector, 'AND')
        self.assertEqual(sorted(q_obj.children), [
            ('distinct__exact', '2'),
            ('foo__exact', '1'),
        ])

        qs.filter().distinct.assert_called_once()

    def test_filter_negation(self):
        q_obj = self.group.build_q_object('negated', '1')
        self.assertEqual(q_obj, ~Q(negated__exact='1'))


class CombinedRequiredGroupTests(ConcreteFilterGroupSanityChecks, TestCase):
    group_class = groups.CombinedRequiredGroup

    test_validation_error = RequiredGroupTests.test_validation_error
    test_validate_none = RequiredGroupTests.test_validate_none
    test_validate_empty = RequiredGroupTests.test_validate_empty
    test_validate_single = RequiredGroupTests.test_validate_single
    test_validate_multiple_partial = RequiredGroupTests.test_validate_multiple_partial
    test_validate_multiple_all = RequiredGroupTests.test_validate_multiple_all

    test_filter_none = CombinedGroupTests.test_filter_none
    test_filter_single = CombinedGroupTests.test_filter_single
    test_filter_multiple = CombinedGroupTests.test_filter_multiple
    test_filter_distinct = CombinedGroupTests.test_filter_distinct
    test_filter_negation = CombinedGroupTests.test_filter_negation
