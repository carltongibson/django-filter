
import functools
import warnings
import mock
from django.test import TestCase

from django_filters import FilterSet
from django_filters.filters import Filter, CharFilter, MethodFilter
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
