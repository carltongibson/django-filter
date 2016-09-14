
import functools
import warnings
import mock
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from django_filters import FilterSet
from django_filters.conf import Settings
from django_filters.filters import Filter, CharFilter, MethodFilter
from django_filters.filterset import STRICTNESS
from .models import User
from .models import NetworkSetting
from .models import SubnetMaskField


def silence(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            f(*args, **kwargs)

    return wrapped


class UserFilter(FilterSet):
    class Meta:
        model = User
        fields = '__all__'


class FilterSetContainerDeprecationTests(TestCase):

    def test__iter__notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            [obj for obj in UserFilter()]

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test__getitem__notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            with self.assertRaises(IndexError):
                UserFilter()[0]

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test__len__notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            len(UserFilter())

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test__count__notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            UserFilter().count()

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))


class MethodFilterDeprecationTests(TestCase):

    def test_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                username = MethodFilter()

                class Meta:
                    model = User
                    fields = []

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    # old tests
    @silence
    def test_filtering(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

        class F(FilterSet):
            username = MethodFilter(action='filter_username')

            class Meta:
                model = User
                fields = ['username']

            def filter_username(self, queryset, value):
                return queryset.filter(
                    username=value
                )

        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': 'alex'}).qs),
                         [User.objects.get(username='alex')])
        self.assertEqual(list(F({'username': 'jose'}).qs),
                         list())

    @silence
    def test_filtering_external(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

        def filter_username(queryset, value):
            return queryset.filter(
                username=value
            )

        class F(FilterSet):
            username = MethodFilter(action=filter_username)

            class Meta:
                model = User
                fields = ['username']

        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': 'alex'}).qs),
                         [User.objects.get(username='alex')])
        self.assertEqual(list(F({'username': 'jose'}).qs),
                         list())

    @silence
    def test_filtering_default_attribute_action(self):
        User.objects.create(username='mike')
        User.objects.create(username='jake')
        User.objects.create(username='aaron')

        class F(FilterSet):
            username = MethodFilter()

            class Meta:
                model = User
                fields = ['username']

            def filter_username(self, queryset, value):
                return queryset.filter(
                    username__contains='ke'
                )

        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': 'mike'}).qs),
                         [User.objects.get(username='mike'),
                          User.objects.get(username='jake')],)
        self.assertEqual(list(F({'username': 'jake'}).qs),
                         [User.objects.get(username='mike'),
                          User.objects.get(username='jake')])
        self.assertEqual(list(F({'username': 'aaron'}).qs),
                         [User.objects.get(username='mike'),
                          User.objects.get(username='jake')])

    @silence
    def test_filtering_default(self):
        User.objects.create(username='mike')
        User.objects.create(username='jake')
        User.objects.create(username='aaron')

        class F(FilterSet):
            username = MethodFilter()
            email = MethodFilter()

            class Meta:
                model = User
                fields = ['username']

        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': 'mike'}).qs),
                         list(User.objects.all()))
        self.assertEqual(list(F({'username': 'jake'}).qs),
                         list(User.objects.all()))
        self.assertEqual(list(F({'username': 'aaron'}).qs),
                         list(User.objects.all()))


class FilterActionDeprecationTests(TestCase):

    def test_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                username = CharFilter(action=lambda x: x)

                class Meta:
                    model = User
                    fields = []

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_filter_using_action(self):
        qs = mock.NonCallableMock(spec=[])
        action = mock.Mock(spec=['filter'])

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            f = Filter(action=action)
            result = f.filter(qs, 'value')
            action.assert_called_once_with(qs, 'value')
            self.assertNotEqual(qs, result)

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_filtering_with_action(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            class F(FilterSet):
                username = CharFilter(action=lambda qs, value: (
                    qs.filter(**{'username__startswith': value})
                ))

                class Meta:
                    model = User
                    fields = ['username']

        f = F({'username': 'a'}, queryset=User.objects.all())
        self.assertQuerysetEqual(
            f.qs, ['alex', 'aaron'], lambda o: o.username, False)


class FilterSetMetaDeprecationTests(TestCase):
    def test_fields_not_set(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = User

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("Not setting Meta.fields with Meta.model is undocumented behavior", str(w[-1].message))

    def test_fields_is_none(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = User
                    fields = None

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("Setting 'Meta.fields = None' is undocumented behavior", str(w[-1].message))

    def test_fields_not_set_ignore_unknown(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = NetworkSetting

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("Not setting Meta.fields with Meta.model is undocumented behavior", str(w[-1].message))

        self.assertNotIn('mask', F.base_filters.keys())

    def test_fields_not_set_with_override(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):

                class Meta:
                    model = NetworkSetting
                    filter_overrides = {
                        SubnetMaskField: {'filter_class': CharFilter},
                    }

            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
            self.assertIn("Not setting Meta.fields with Meta.model is undocumented behavior", str(w[-1].message))

        self.assertEqual(list(F.base_filters.keys()), ['ip', 'mask'])


class StrictnessDeprecationTests(TestCase):
    def test_notification(self):

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                strict = False

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_passthrough(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            class F(FilterSet):
                strict = False

            self.assertEqual(F._meta.strict, False)


class FilterOverridesDeprecationTests(TestCase):

    def test_notification(self):

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                filter_overrides = {}

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_passthrough(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            class F(FilterSet):
                filter_overrides = {
                    SubnetMaskField: {'filter_class': CharFilter},
                }

                class Meta:
                    model = NetworkSetting
                    fields = '__all__'

        self.assertDictEqual(F._meta.filter_overrides, {
            SubnetMaskField: {'filter_class': CharFilter},
        })

        self.assertEqual(list(F.base_filters.keys()), ['ip', 'mask'])


class OrderByFieldDeprecationTests(TestCase):
    def test_notification(self):

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                order_by_field = 'field'

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_passthrough(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            class F(FilterSet):
                order_by_field = 'field'

            self.assertEqual(F._meta.order_by_field, 'field')


class OrderByDeprecationTests(TestCase):
    def test_order_by_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    order_by = True

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_order_by_field_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    order_by_field = 'field'

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_get_order_by_assertion(self):
        with self.assertRaises(AssertionError):
            class F(FilterSet):
                def get_order_by(self):
                    pass

    def test_get_ordering_field_assertion(self):
        with self.assertRaises(AssertionError):
            class F(FilterSet):
                def get_ordering_field(self):
                    pass


class DeprecatedOrderingFilterSetTests(TestCase):
    def setUp(self):
        self.alex = User.objects.create(username='alex', status=1)
        self.jacob = User.objects.create(username='jacob', status=2)
        self.aaron = User.objects.create(username='aaron', status=2)
        self.carl = User.objects.create(username='carl', status=0)
        self.qs = User.objects.all().order_by('id')

    # old filterset tests
    @silence
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

    @silence
    def test_ordering_on_unknown_value(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']

        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, [], lambda o: o.username)

    @silence
    def test_ordering_on_unknown_value_results_in_default_ordering_without_strict(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']
                strict = STRICTNESS.IGNORE

        self.assertFalse(F._meta.strict)
        f = F({'o': 'username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['alex', 'jacob', 'aaron', 'carl'], lambda o: o.username)

    @silence
    def test_ordering_on_unknown_value_results_in_default_ordering_with_strict_raise(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']
                strict = STRICTNESS.RAISE_VALIDATION_ERROR

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

    @silence
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

    @silence
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

    @silence
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

    @silence
    def test_ordering_with_overridden_field_name(self):
        """
        Set the `order_by_field` on the filterset and ensure that the
        field name is respected.
        """
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']
                order_by_field = 'order'

        f = F({'order': 'status'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['carl', 'alex', 'jacob', 'aaron'], lambda o: o.username)

    @silence
    def test_ordering_descending_set(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['username', '-username']

        f = F({'o': '-username'}, queryset=self.qs)
        self.assertQuerysetEqual(
            f.qs, ['jacob', 'carl', 'alex', 'aaron'], lambda o: o.username)

    @silence
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


class DeprecatedOrderingFormTests(TestCase):
    @silence
    def test_ordering(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']

        f = F().form
        self.assertEqual(len(f.fields), 3)
        self.assertIn('o', f.fields)
        self.assertEqual(f.fields['o'].choices, [('status', 'Status')])

    @silence
    def test_ordering_uses_all_fields(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True

        f = F().form
        self.assertEqual(f.fields['o'].choices, [
            ('username', 'Username'),
            ('-username', 'Username (descending)'),
            ('status', 'Status'),
            ('-status', 'Status (descending)')])

    @silence
    def test_ordering_uses_filter_label(self):
        class F(FilterSet):
            username = CharFilter(label='Account')

            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True

        f = F().form
        self.assertEqual(f.fields['o'].choices, [
            ('username', 'Account'),
            ('-username', 'Account (descending)'),
            ('status', 'Status'),
            ('-status', 'Status (descending)')])

    @silence
    def test_ordering_uses_explicit_filter_name(self):
        class F(FilterSet):
            account = CharFilter(name='username')

            class Meta:
                model = User
                fields = ['account', 'status']
                order_by = True

        f = F().form
        self.assertEqual(f.fields['o'].choices, [
            ('account', 'Account'),
            ('-account', 'Account (descending)'),
            ('status', 'Status'),
            ('-status', 'Status (descending)')])

    @silence
    def test_ordering_with_overridden_field_name(self):
        """
        Set the `order_by_field` on the filterset and ensure that the
        field name is respected.
        """
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']
                order_by_field = 'order'

        f = F().form
        self.assertNotIn('o', f.fields)
        self.assertIn('order', f.fields)
        self.assertEqual(f.fields['order'].choices, [('status', 'Status')])

    @silence
    def test_ordering_with_overridden_field_name_and_descending(self):
        """
        Set the `order_by_field` on the filterset and ensure that the
        field name is respected.
        """
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status', '-status']
                order_by_field = 'order'

        f = F().form
        self.assertNotIn('o', f.fields)
        self.assertIn('order', f.fields)
        self.assertEqual(f.fields['order'].choices, [('status', 'Status'), ('-status', 'Status (descending)')])

    @silence
    def test_ordering_with_overridden_field_name_and_using_all_fields(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True
                order_by_field = 'order'

        f = F().form
        self.assertIn('order', f.fields)
        self.assertEqual(f.fields['order'].choices, [
            ('username', 'Username'),
            ('-username', 'Username (descending)'),
            ('status', 'Status'),
            ('-status', 'Status (descending)')])

    @silence
    def test_ordering_with_custom_display_names(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = [('status', 'Current status')]

        f = F().form
        self.assertEqual(
            f.fields['o'].choices, [('status', 'Current status')])


class DeprecatedSettingsTests(TestCase):

    def test_filter_help_text(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            with override_settings(FILTERS_HELP_TEXT_FILTER=False):
                Settings()

        self.assertEqual(len(w), 1)
        self.assertIn("The 'FILTERS_HELP_TEXT_FILTER' setting has been deprecated.", str(w[0].message))

    def test_exclude_help_text(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            with override_settings(FILTERS_HELP_TEXT_EXCLUDE=False):
                Settings()

        self.assertEqual(len(w), 1)
        self.assertIn("The 'FILTERS_HELP_TEXT_EXCLUDE' setting has been deprecated.", str(w[0].message))
