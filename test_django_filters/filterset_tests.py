from __future__ import absolute_import
from __future__ import unicode_literals

import mock
import datetime
from django.db import models
from django.utils import unittest
from django.test import TestCase
from django.utils import six
from django.utils.timezone import now
from django.utils import timezone

from django_filters.filterset import FilterSet
from django_filters.filterset import FILTER_FOR_DBFIELD_DEFAULTS
from django_filters.filters import AllValuesFilter
from django_filters.filters import CharFilter
from django_filters.filters import ChoiceFilter
from django_filters.filters import DateRangeFilter
# from django_filters.filters import DateTimeFilter
from django_filters.filters import MultipleChoiceFilter
from django_filters.filters import NumberFilter
from django_filters.filters import RangeFilter
# from django_filters.widgets import LinkWidget

from .models import User
from .models import Comment
from .models import Book
from .models import Restaurant
from .models import Article
from .models import NetworkSetting
from .models import SubnetMaskField
from .models import Company
from .models import Location
from .models import STATUS_CHOICES


class HelperMethodsTests(TestCase):

    @unittest.skip('todo')
    def test_get_declared_filters(self):
        pass

    @unittest.skip('todo')
    def test_get_model_field(self):
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

    @unittest.skip('todo')
    def test_filter_found_for_field(self):
        pass

    @unittest.skip('todo')
    def test_filter_not_found_for_field(self):
        pass

    @unittest.skip('todo')
    def test_filter_for_field_with_extras(self):
        pass

    @unittest.skip('todo')
    def test_filter_for_field_with_choices(self):
        pass

    def test_filter_for_field_that_is_subclassed(self):
        f = User._meta.get_field('first_name')
        result = FilterSet.filter_for_field(f, 'first_name')
        self.assertIsInstance(result, CharFilter)

    @unittest.skip('todo')
    def test_filter_overrides(self):
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

        self.assertEquals(set(F.base_filters), set(['name', 'serves_pizza']))

        class F(FilterSet):
            class Meta:
                model = Restaurant
                fields = ['name', 'serves_pizza']

        self.assertEquals(set(F.base_filters), set(['name', 'serves_pizza']))

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


class CharFilterTests(TestCase):

    def test_filtering(self):
        b1 = Book.objects.create(
            title="Ender's Game", price='1.00', average_rating=3.0)
        b2 = Book.objects.create(
            title="Rainbow Six", price='1.00', average_rating=3.0)
        b3 = Book.objects.create(
            title="Snowcrash", price='1.00', average_rating=3.0)

        class F(FilterSet):
            class Meta:
                model = Book
                fields = ['title']

        qs = Book.objects.all()
        f = F(queryset=qs)
        self.assertQuerysetEqual(f.qs, [b1.pk, b2.pk, b3.pk],
                                 lambda o: o.pk, ordered=False)
        f = F({'title': 'Snowcrash'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [b3.pk], lambda o: o.pk)


class BooleanFilterTests(TestCase):

    def test_filtering(self):
        User.objects.create(username='alex', is_active=False)
        User.objects.create(username='jacob', is_active=True)
        User.objects.create(username='aaron', is_active=False)

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['is_active']

        qs = User.objects.all()
        
        # '2' and '3' are how the field expects the data from the browser
        f = F({'is_active': '2'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['jacob'], lambda o: o.username, False)
        
        f = F({'is_active': '3'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['alex', 'aaron'],
                                 lambda o: o.username, False)
        
        f = F({'is_active': '1'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['alex', 'aaron', 'jacob'],
                                 lambda o: o.username, False)


class ChoiceFilterTests(TestCase):

    def test_filtering(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status']

        f = F()
        self.assertQuerysetEqual(f.qs,
                                 ['aaron', 'alex', 'jacob', 'carl'],
                                 lambda o: o.username, False)
        f = F({'status': '1'})
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username, False)

        f = F({'status': '2'})
        self.assertQuerysetEqual(f.qs, ['jacob', 'aaron'],
                                 lambda o: o.username, False)

        f = F({'status': '0'})
        self.assertQuerysetEqual(f.qs, ['carl'], lambda o: o.username, False)


class MultipleChoiceFilterTests(TestCase):

    def test_filtering(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        class F(FilterSet):
            status = MultipleChoiceFilter(choices=STATUS_CHOICES)

            class Meta:
                model = User
                fields = ['status']

        qs = User.objects.all().order_by('username')
        f = F(queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ['aaron', 'jacob', 'alex', 'carl'],
            lambda o: o.username, False)

        f = F({'status': ['0']}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ['carl'], lambda o: o.username)
        
        f = F({'status': ['0', '1']}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ['alex', 'carl'], lambda o: o.username)

        f = F({'status': ['0', '1', '2']}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ['aaron', 'alex', 'carl', 'jacob'], lambda o: o.username)


class DateFilterTests(TestCase):

    def test_filtering(self):
        today = now().date()
        timestamp = now().time().replace(microsecond=0)
        last_week = today - datetime.timedelta(days=7)
        check_date = six.text_type(last_week)
        u = User.objects.create(username='alex')
        Comment.objects.create(author=u, time=timestamp, date=today)
        Comment.objects.create(author=u, time=timestamp, date=last_week)
        Comment.objects.create(author=u, time=timestamp, date=today)
        Comment.objects.create(author=u, time=timestamp, date=last_week)

        class F(FilterSet):
            class Meta:
                model = Comment
                fields = ['date']

        f = F({'date': check_date}, queryset=Comment.objects.all())
        self.assertEqual(len(f.qs), 2)
        self.assertQuerysetEqual(f.qs, [2, 4], lambda o: o.pk)


class TimeFilterTests(TestCase):

    def test_filtering(self):
        today = now().date()
        now_time = now().time().replace(microsecond=0)
        ten_min_ago = (now() - datetime.timedelta(minutes=10))
        fixed_time = ten_min_ago.time().replace(microsecond=0)
        check_time = six.text_type(fixed_time)
        u = User.objects.create(username='alex')
        Comment.objects.create(author=u, time=now_time, date=today)
        Comment.objects.create(author=u, time=fixed_time, date=today)
        Comment.objects.create(author=u, time=now_time, date=today)
        Comment.objects.create(author=u, time=fixed_time, date=today)

        class F(FilterSet):
            class Meta:
                model = Comment
                fields = ['time']

        f = F({'time': check_time}, queryset=Comment.objects.all())
        self.assertEqual(len(f.qs), 2)
        self.assertQuerysetEqual(f.qs, [2, 4], lambda o: o.pk)


class DateTimeFilterTests(TestCase):

    def test_filtering(self):
        now_dt = now()
        ten_min_ago = now_dt - datetime.timedelta(minutes=10)
        one_day_ago = now_dt - datetime.timedelta(days=1)
        u = User.objects.create(username='alex')
        Article.objects.create(author=u, published=now_dt)
        Article.objects.create(author=u, published=ten_min_ago)
        Article.objects.create(author=u, published=one_day_ago)

        tz = timezone.get_current_timezone()
        # make naive, like a browser would send
        local_ten_min_ago = timezone.make_naive(ten_min_ago, tz)
        check_dt = six.text_type(local_ten_min_ago)

        class F(FilterSet):
            class Meta:
                model = Article
                fields = ['published']

        qs = Article.objects.all()
        f = F({'published': ten_min_ago}, queryset=qs)
        self.assertEqual(len(f.qs), 1)
        self.assertQuerysetEqual(f.qs, [2], lambda o: o.pk)

        # this is how it would come through a browser
        f = F({'published': check_dt}, queryset=qs)
        self.assertEqual(len(f.qs), 1,
            "%s isn't matching %s when cleaned" % (check_dt, ten_min_ago))
        self.assertQuerysetEqual(f.qs, [2], lambda o: o.pk)


class ModelChoiceFilterTests(TestCase):

    def test_filtering(self):
        alex = User.objects.create(username='alex')
        jacob = User.objects.create(username='jacob')
        date = now().date()
        time = now().time()
        Comment.objects.create(author=jacob, time=time, date=date)
        Comment.objects.create(author=alex, time=time, date=date)
        Comment.objects.create(author=jacob, time=time, date=date)

        class F(FilterSet):
            class Meta:
                model = Comment
                fields = ['author']

        qs = Comment.objects.all()
        f = F({'author': jacob.pk}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [1, 3], lambda o: o.pk)


class ModelMultipleChoiceFilterTests(TestCase):

    def setUp(self):
        alex = User.objects.create(username='alex')
        User.objects.create(username='jacob')
        aaron = User.objects.create(username='aaron')
        b1 = Book.objects.create(title="Ender's Game", price='1.00',
                                 average_rating=3.0)
        b2 = Book.objects.create(title="Rainbow Six", price='1.00',
                                 average_rating=3.0)
        b3 = Book.objects.create(title="Snowcrash", price='1.00',
                                 average_rating=3.0)
        Book.objects.create(title="Stranger in a Strage Land", price='1.00',
                            average_rating=3.0)
        alex.favorite_books = [b1, b2]
        aaron.favorite_books = [b1, b3]

    def test_filtering(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['favorite_books']

        qs = User.objects.all().order_by('username')
        f = F({'favorite_books': ['1']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['aaron', 'alex'], lambda o: o.username)
        
        f = F({'favorite_books': ['1', '3']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['aaron', 'alex'], lambda o: o.username)
        
        f = F({'favorite_books': ['2']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

        f = F({'favorite_books': ['4']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [], lambda o: o.username)


class NumberFilterTests(TestCase):

    def setUp(self):
        Book.objects.create(title="Ender's Game", price='10.0',
                            average_rating=4.7999999999999998)
        Book.objects.create(title="Rainbow Six", price='15.0',
                            average_rating=4.5999999999999996)
        Book.objects.create(title="Snowcrash", price='20.0',
                            average_rating=4.2999999999999998)

    def test_filtering(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ['price']

        f = F({'price': 10}, queryset=Book.objects.all())
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game'], lambda o: o.title)

    def test_filtering_with_single_lookup_type(self):
        class F(FilterSet):
            price = NumberFilter(lookup_type='lt')

            class Meta:
                model = Book
                fields = ['price']

        f = F({'price': 16}, queryset=Book.objects.all().order_by('title'))
        self.assertQuerysetEqual(
            f.qs, ['Ender\'s Game', 'Rainbow Six'], lambda o: o.title)

    def test_filtering_with_multiple_lookup_types(self):
        class F(FilterSet):
            price = NumberFilter(lookup_type=['lt', 'gt'])

            class Meta:
                model = Book
                fields = ['price']

        qs = Book.objects.all()
        f = F({'price_0': '15', 'price_1': 'lt'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game'], lambda o: o.title)
        f = F({'price_0': '15', 'price_1': 'lt'})
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game'], lambda o: o.title)
        f = F({'price_0': '', 'price_1': 'lt'})
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Rainbow Six', 'Snowcrash'],
                                 lambda o: o.title, ordered=False)

        class F(FilterSet):
            price = NumberFilter(lookup_type=['lt', 'gt', 'exact'])

            class Meta:
                model = Book
                fields = ['price']

        f = F({'price_0': '15'})
        self.assertQuerysetEqual(f.qs, ['Rainbow Six'], lambda o: o.title)


class RangeFilterTests(TestCase):

    def setUp(self):
        Book.objects.create(title="Ender's Game", price='10.0',
                            average_rating=4.7999999999999998)
        Book.objects.create(title="Rainbow Six", price='15.0',
                            average_rating=4.5999999999999996)
        Book.objects.create(title="Snowcrash", price='20.0',
                            average_rating=4.2999999999999998)

    def test_filtering(self):
        class F(FilterSet):
            price = RangeFilter()

            class Meta:
                model = Book
                fields = ['price']

        qs = Book.objects.all().order_by('title')
        f = F(queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Rainbow Six', 'Snowcrash'],
                                 lambda o: o.title)
        f = F({'price_0': '5', 'price_1': '15'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Rainbow Six'],
                                 lambda o: o.title)


@unittest.skip('date-range is funky')
class DateRangeFilterTests(TestCase):

    def setUp(self):
        today = now().date()
        five_days_ago = today - datetime.timedelta(days=5)
        two_weeks_ago = today - datetime.timedelta(days=14)
        two_months_ago = today - datetime.timedelta(days=62)
        two_years_ago = today - datetime.timedelta(days=800)
        alex = User.objects.create(username='alex')
        time = now().time()
        Comment.objects.create(date=two_weeks_ago, author=alex, time=time)
        Comment.objects.create(date=two_years_ago, author=alex, time=time)
        Comment.objects.create(date=five_days_ago, author=alex, time=time)
        Comment.objects.create(date=today, author=alex, time=time)
        Comment.objects.create(date=two_months_ago, author=alex, time=time)

    def test_filtering_for_year(self):
        class F(FilterSet):
            date = DateRangeFilter()

            class Meta:
                model = Comment
                fields = ['date']
        
        f = F({'date': '4'})  # this year
        self.assertQuerysetEqual(f.qs, [1, 3, 4, 5], lambda o: o.pk, False)

    def test_filtering_for_month(self):
        class F(FilterSet):
            date = DateRangeFilter()

            class Meta:
                model = Comment
                fields = ['date']
        
        f = F({'date': '3'})  # this month
        self.assertQuerysetEqual(f.qs, [1, 3, 4], lambda o: o.pk, False)

    @unittest.expectedFailure
    def test_filtering_for_week(self):
        class F(FilterSet):
            date = DateRangeFilter()

            class Meta:
                model = Comment
                fields = ['date']

        f = F({'date': '2'})  # this week
        self.assertQuerysetEqual(f.qs, [3, 4], lambda o: o.pk, False)

    def test_filtering_for_today(self):
        class F(FilterSet):
            date = DateRangeFilter()

            class Meta:
                model = Comment
                fields = ['date']

        f = F({'date': '1'})  # today
        self.assertQuerysetEqual(f.qs, [4], lambda o: o.pk, False)

    # it will be difficult to test for TZ related issues, where "today" means
    # different things to both user and server.


class AllValuesFilterTests(TestCase):

    def test_filtering(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

        class F(FilterSet):
            username = AllValuesFilter()

            class Meta:
                model = User
                fields = ['username']

        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': 'alex'})),
                         [User.objects.get(username='alex')])
        self.assertEqual(list(F({'username': 'jose'})),
                         list(User.objects.all()))


class RelatedObjectTests(TestCase):

    @unittest.skip('todo')
    def test_o2o_relation(self):
        pass

    @unittest.skip('todo')
    def test_reverse_o2o_relation(self):
        pass

    @unittest.skip('todo')
    def test_o2o_relation_attribute(self):
        pass

    @unittest.skip('todo')
    def test_reverse_o2o_relation_attribute(self):
        pass

    @unittest.skip('todo')
    def test_fk_relation(self):
        pass

    def test_reverse_fk_relation(self):
        alex = User.objects.create(username='alex')
        jacob = User.objects.create(username='jacob')
        date = now().date()
        time = now().time()
        Comment.objects.create(text='comment 1',
                               author=jacob, time=time, date=date)
        Comment.objects.create(text='comment 2',
                               author=alex, time=time, date=date)
        Comment.objects.create(text='comment 3',
                               author=jacob, time=time, date=date)

        with self.assertRaises(AttributeError):
            class F(FilterSet):
                class Meta:
                    model = User
                    fields = ['comments']

        # qs = User.objects.all()
        # f = F({'comment': 2}, queryset=qs)
        # self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

        with self.assertRaises(AttributeError):
            class F(FilterSet):
                comment = AllValuesFilter()

                class Meta:
                    model = User
                    fields = ['comments']

        # f = F({'comments': 2}, queryset=qs)
        # self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

    def test_fk_relation_attribute(self):
        now_dt = now()
        alex = User.objects.create(username='alex')
        jacob = User.objects.create(username='jacob')
        User.objects.create(username='aaron')
        
        Article.objects.create(author=alex, published=now_dt)
        Article.objects.create(author=jacob, published=now_dt)
        Article.objects.create(author=alex, published=now_dt)

        class F(FilterSet):
            class Meta:
                model = Article
                fields = ['author__username']
        
        self.assertEqual(list(F.base_filters), ['author__username'])
        self.assertEqual(F({'author__username': 'alex'}).qs.count(), 2)
        self.assertEqual(F({'author__username': 'jacob'}).qs.count(), 1)

        class F(FilterSet):
            author__username = AllValuesFilter()

            class Meta:
                model = Article
                fields = ['author__username']

        self.assertEqual(F({'author__username': 'alex'}).qs.count(), 2)

    def test_reverse_fk_relation_attribute(self):
        alex = User.objects.create(username='alex')
        jacob = User.objects.create(username='jacob')
        date = now().date()
        time = now().time()
        Comment.objects.create(text='comment 1',
                               author=jacob, time=time, date=date)
        Comment.objects.create(text='comment 2',
                               author=alex, time=time, date=date)
        Comment.objects.create(text='comment 3',
                               author=jacob, time=time, date=date)

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['comments__text']

        qs = User.objects.all()
        f = F({'comments__text': 'comment 2'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

        class F(FilterSet):
            comments__text = AllValuesFilter()

            class Meta:
                model = User
                fields = ['comments__text']

        f = F({'comments__text': 'comment 2'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

    @unittest.skip('todo')
    def test_m2m_relation(self):
        pass

    def test_reverse_m2m_relation(self):
        alex = User.objects.create(username='alex')
        User.objects.create(username='jacob')
        aaron = User.objects.create(username='aaron')
        b1 = Book.objects.create(title="Ender's Game", price='1.00',
                                 average_rating=3.0)
        b2 = Book.objects.create(title="Rainbow Six", price='1.00',
                                 average_rating=3.0)
        b3 = Book.objects.create(title="Snowcrash", price='1.00',
                                 average_rating=3.0)
        Book.objects.create(title="Stranger in a Strage Land", price='1.00',
                            average_rating=3.0)
        alex.favorite_books = [b1, b2]
        aaron.favorite_books = [b1, b3]

        with self.assertRaises(AttributeError):
            class F(FilterSet):
                class Meta:
                    model = Book
                    fields = ['lovers']

        # qs = User.objects.all()
        # f = F({'lovers': [1]}, queryset=qs)
        # self.assertQuerysetEqual(
        #     f.qs, ["Ender's Game", "Rainbow Six"], lambda o: o.title)

        with self.assertRaises(AttributeError):
            class F(FilterSet):
                lovers = AllValuesFilter()

                class Meta:
                    model = Book
                    fields = ['lovers']

        # f = F({'lovers': 1}, queryset=qs)
        # self.assertQuerysetEqual(
        #     f.qs, ["Ender's Game", "Rainbow Six"], lambda o: o.title)

    def test_m2m_relation_attribute(self):
        alex = User.objects.create(username='alex')
        User.objects.create(username='jacob')
        aaron = User.objects.create(username='aaron')
        b1 = Book.objects.create(title="Ender's Game", price='1.00',
                                 average_rating=3.0)
        b2 = Book.objects.create(title="Rainbow Six", price='1.00',
                                 average_rating=3.0)
        b3 = Book.objects.create(title="Snowcrash", price='1.00',
                                 average_rating=3.0)
        Book.objects.create(title="Stranger in a Strage Land", price='1.00',
                            average_rating=3.0)
        alex.favorite_books = [b1, b2]
        aaron.favorite_books = [b1, b3]

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['favorite_books__title']

        qs = User.objects.all().order_by('username')
        f = F({'favorite_books__title': "Ender's Game"}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['aaron', 'alex'], lambda o: o.username)
        
        f = F({'favorite_books__title': 'Rainbow Six'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

        class F(FilterSet):
            favorite_books__title = MultipleChoiceFilter()

            class Meta:
                model = User
                fields = ['favorite_books__title']
        
        f = F()
        self.assertEqual(
            len(f.filters['favorite_books__title'].field.choices), 0)
        # f = F({'favorite_books__title': ['1', '3']},
        #     queryset=qs)
        # self.assertQuerysetEqual(
        #     f.qs, ['aaron', 'alex'], lambda o: o.username)

        class F(FilterSet):
            favorite_books__title = AllValuesFilter()

            class Meta:
                model = User
                fields = ['favorite_books__title']

        f = F({'favorite_books__title': "Snowcrash"}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['aaron'], lambda o: o.username)

    def test_reverse_m2m_relation_attribute(self):
        alex = User.objects.create(username='alex')
        User.objects.create(username='jacob')
        aaron = User.objects.create(username='aaron')
        b1 = Book.objects.create(title="Ender's Game", price='1.00',
                                 average_rating=3.0)
        b2 = Book.objects.create(title="Rainbow Six", price='1.00',
                                 average_rating=3.0)
        b3 = Book.objects.create(title="Snowcrash", price='1.00',
                                 average_rating=3.0)
        Book.objects.create(title="Stranger in a Strage Land", price='1.00',
                            average_rating=3.0)
        alex.favorite_books = [b1, b2]
        aaron.favorite_books = [b1, b3]

        class F(FilterSet):
            class Meta:
                model = Book
                fields = ['lovers__username']

        qs = Book.objects.all().order_by('title')
        f = F({'lovers__username': "alex"}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ["Ender's Game", "Rainbow Six"], lambda o: o.title)
        
        f = F({'lovers__username': 'jacob'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [], lambda o: o.title)

        class F(FilterSet):
            lovers__username = MultipleChoiceFilter()

            class Meta:
                model = Book
                fields = ['lovers__username']
        
        f = F()
        self.assertEqual(
            len(f.filters['lovers__username'].field.choices), 0)
        # f = F({'lovers__username': ['1', '3']},
        #     queryset=qs)
        # self.assertQuerysetEqual(
        #     f.qs, ["Ender's Game", "Rainbow Six"], lambda o: o.title)

        class F(FilterSet):
            lovers__username = AllValuesFilter()

            class Meta:
                model = Book
                fields = ['lovers__username']

        f = F({'lovers__username': "alex"}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ["Ender's Game", "Rainbow Six"], lambda o: o.title)

    @unittest.skip('todo')
    def test_fk_relation_on_m2m_relation(self):
        pass

    @unittest.skip('todo')
    def test_fk_relation_attribute_on_m2m_relation(self):
        pass


class ProblematicBehaviorTests(TestCase):

    def setUp(self):
        company = Company.objects.create(name='company')
        Location.objects.create(
            company=company, open_days="some", zip_code="90210")
        Location.objects.create(
            company=company, open_days="WEEKEND", zip_code="11111")

    @unittest.expectedFailure
    def test_related_attributes_filter_differently(self):
        class F(FilterSet):
            class Meta:
                model = Company
                fields = ('locations__zip_code', 'locations__open_days')

        f = F({'locations__zip_code': '90210',
               'locations__open_days': 'WEEKEND'})
        self.assertEqual(f.qs.count(), 0)


class FilterSetTests(TestCase):

    def test_filtering_with_declared_filters(self):
        class F(FilterSet):
            account = CharFilter(name='username')

            class Meta:
                model = User
                fields = ['account']

        qs = mock.MagicMock()
        f = F({'account': 'jdoe'}, queryset=qs)
        result = f.qs
        self.assertNotEqual(qs, result)
        qs.all.return_value.filter.assert_called_with(username__exact='jdoe')

    def test_filtering_with_multiple_filters(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status', 'username']

        qs = User.objects.all()
        
        f = F({'username': 'alex', 'status': '1'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

        f = F({'username': 'alex', 'status': '2'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [], lambda o: o.pk)

    def test_filter_with_action(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

        class F(FilterSet):
            username = CharFilter(action=lambda qs, value: (
                qs.filter(**{'username__startswith': value})))

            class Meta:
                model = User
                fields = ['username']

        f = F({'username': 'a'}, queryset=User.objects.all())
        self.assertQuerysetEqual(
            f.qs, ['alex', 'aaron'], lambda o: o.username, False)

    def test_filter_with_initial(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        class F(FilterSet):
            status = ChoiceFilter(choices=STATUS_CHOICES, initial=1)

            class Meta:
                model = User
                fields = ['status']

        qs = User.objects.all()
        f = F(queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

        f = F({'status': 0}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['carl'], lambda o: o.username)
    
    def test_qs_count(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status']

        qs = User.objects.all()
        f = F(queryset=qs)
        self.assertEqual(len(f.qs), 4)
        self.assertEqual(f.count(), 4)

        f = F({'status': '0'}, queryset=qs)
        self.assertEqual(len(f.qs), 1)
        self.assertEqual(f.count(), 1)

        f = F({'status': '1'}, queryset=qs)
        self.assertEqual(len(f.qs), 1)
        self.assertEqual(f.count(), 1)

        f = F({'status': '2'}, queryset=qs)
        self.assertEqual(len(f.qs), 2)
        self.assertEqual(f.count(), 2)


class FilterSetOrdering(TestCase):

    def setUp(self):
        self.alex = User.objects.create(username='alex', status=1)
        self.jacob = User.objects.create(username='jacob', status=2)
        self.aaron = User.objects.create(username='aaron', status=2)
        self.carl = User.objects.create(username='carl', status=0)
        # user_ids = list(User.objects.all().values_list('pk', flat=True))
        self.qs = User.objects.all()

    def test_ordering_unset(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']
        
        f = F({}, queryset=self.qs)
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

