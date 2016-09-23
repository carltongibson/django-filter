from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import mock
import unittest

import django
from django import forms
from django.test import TestCase, override_settings
from django.utils import six
from django.utils.timezone import now
from django.utils import timezone

from django_filters.filterset import FilterSet
from django_filters.filters import AllValuesFilter
from django_filters.filters import AllValuesMultipleFilter
from django_filters.filters import CharFilter
from django_filters.filters import ChoiceFilter
from django_filters.filters import DateRangeFilter
from django_filters.filters import DateFromToRangeFilter
from django_filters.filters import DateTimeFromToRangeFilter
# from django_filters.filters import DateTimeFilter
from django_filters.filters import DurationFilter
from django_filters.filters import MultipleChoiceFilter
from django_filters.filters import ModelMultipleChoiceFilter
from django_filters.filters import NumberFilter
from django_filters.filters import OrderingFilter
from django_filters.filters import RangeFilter
from django_filters.filters import TimeRangeFilter
# from django_filters.widgets import LinkWidget
from django_filters.exceptions import FieldLookupError

from .models import User
from .models import Comment
from .models import Book
# from .models import Restaurant
from .models import Article
# from .models import NetworkSetting
# from .models import SubnetMaskField
from .models import Company
from .models import Location
from .models import Account
from .models import BankAccount
from .models import Profile
from .models import Node
from .models import DirectedNode
from .models import STATUS_CHOICES
from .models import SpacewalkRecord


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


class IntegerFilterTest(TestCase):

    def test_filtering(self):
        default_values = {
            'in_good_standing': True,
            'friendly': False,
        }
        b1 = BankAccount.objects.create(amount_saved=0, **default_values)
        b2 = BankAccount.objects.create(amount_saved=3, **default_values)
        b3 = BankAccount.objects.create(amount_saved=10, **default_values)

        class F(FilterSet):
            class Meta:
                model = BankAccount
                fields = ['amount_saved']

        qs = BankAccount.objects.all()
        f = F(queryset=qs)
        self.assertQuerysetEqual(f.qs, [b1.pk, b2.pk, b3.pk],
                                 lambda o: o.pk, ordered=False)
        f = F({'amount_saved': '10'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [b3.pk], lambda o: o.pk)
        f = F({'amount_saved': '0'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [b1.pk], lambda o: o.pk)


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

    def test_filtering_on_explicitly_defined_field(self):
        """
        Test for #30.

        If you explicitly declare ChoiceFilter fields you **MUST** pass `choices`.
        """
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        class F(FilterSet):
            status = ChoiceFilter(choices=STATUS_CHOICES)

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
        self.assertQuerysetEqual(f.qs, [2, 4], lambda o: o.pk, False)


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
        self.assertQuerysetEqual(f.qs, [2, 4], lambda o: o.pk, False)


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
        self.assertEqual(
            len(f.qs),
            1,
            "%s isn't matching %s when cleaned" % (check_dt, ten_min_ago))
        self.assertQuerysetEqual(f.qs, [2], lambda o: o.pk)


class DurationFilterTests(TestCase):
    """Duration filter tests.

    The preferred format for durations in Django is '%d %H:%M:%S.%f'.
    See django.utils.dateparse.parse_duration

    Django is not fully ISO 8601 compliant (yet): year, month, and
    week designators are not supported, so a duration string
    like "P3Y6M4DT12H30M5S" cannot be used.
    See https://en.wikipedia.org/wiki/ISO_8601#Durations

    """
    def setUp(self):
        self.r1 = SpacewalkRecord.objects.create(
            astronaut="Anatoly Solovyev",
            duration=datetime.timedelta(hours=82, minutes=22))
        self.r2 = SpacewalkRecord.objects.create(
            astronaut="Michael Lopez-Alegria",
            duration=datetime.timedelta(hours=67, minutes=40))
        self.r3 = SpacewalkRecord.objects.create(
            astronaut="Jerry L. Ross",
            duration=datetime.timedelta(hours=58, minutes=32))
        self.r4 = SpacewalkRecord.objects.create(
            astronaut="John M. Grunsfeld",
            duration=datetime.timedelta(hours=58, minutes=30))
        self.r5 = SpacewalkRecord.objects.create(
            astronaut="Richard Mastracchio",
            duration=datetime.timedelta(hours=53, minutes=4))

    def test_filtering(self):

        class F(FilterSet):
            class Meta:
                model = SpacewalkRecord
                fields = ['duration']

        qs = SpacewalkRecord.objects.all()

        # Django style: 3 days, 10 hours, 22 minutes.
        f = F({'duration': '3 10:22:00'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [self.r1], lambda x: x)

        # ISO 8601: 3 days, 10 hours, 22 minutes.
        f = F({'duration': 'P3DT10H22M'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [self.r1], lambda x: x)

        # Django style: 82 hours, 22 minutes.
        f = F({'duration': '82:22:00'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [self.r1], lambda x: x)

        # ISO 8601: 82 hours, 22 minutes.
        f = F({'duration': 'PT82H22M'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [self.r1], lambda x: x)

    def test_filtering_with_single_lookup_expr_dictionary(self):

        class F(FilterSet):
            class Meta:
                model = SpacewalkRecord
                fields = {'duration': ['gt', 'gte', 'lt', 'lte']}

        qs = SpacewalkRecord.objects.order_by('-duration')

        f = F({'duration__gt': 'PT58H30M'}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, [self.r1, self.r2, self.r3], lambda x: x)

        f = F({'duration__gte': 'PT58H30M'}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, [self.r1, self.r2, self.r3, self.r4], lambda x: x)

        f = F({'duration__lt': 'PT58H30M'}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, [self.r5], lambda x: x)

        f = F({'duration__lte': 'PT58H30M'}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, [self.r4, self.r5], lambda x: x)

    def test_filtering_with_multiple_lookup_exprs(self):

        class F(FilterSet):
            min_duration = DurationFilter(name='duration', lookup_expr='gte')
            max_duration = DurationFilter(name='duration', lookup_expr='lte')

            class Meta:
                model = SpacewalkRecord
                fields = '__all__'

        qs = SpacewalkRecord.objects.order_by('duration')

        f = F({'min_duration': 'PT55H', 'max_duration': 'PT60H'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [self.r4, self.r3], lambda x: x)


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
        self.assertQuerysetEqual(f.qs, [1, 3], lambda o: o.pk, False)


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

        self.alex = alex

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

    def test_filtering_dictionary(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = {'favorite_books': ['exact']}

        qs = User.objects.all().order_by('username')
        f = F({'favorite_books': ['1']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['aaron', 'alex'], lambda o: o.username)

        f = F({'favorite_books': ['1', '3']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['aaron', 'alex'], lambda o: o.username)

        f = F({'favorite_books': ['2']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

        f = F({'favorite_books': ['4']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [], lambda o: o.username)

    def test_filtering_on_all_of_subset_of_choices(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['favorite_books']

            def __init__(self, *args, **kwargs):
                super(F, self).__init__(*args, **kwargs)
                # This filter has a limited number of choices.
                self.filters['favorite_books'].extra.update({
                    'queryset': Book.objects.filter(id__in=[1, 2])
                })

                self.filters['favorite_books'].required = True

        qs = User.objects.all().order_by('username')

        # Select all the given choices.
        f = F({'favorite_books': ['1', '2']}, queryset=qs)

        # The results should only include matching users - not Jacob.
        self.assertQuerysetEqual(f.qs, ['aaron', 'alex'], lambda o: o.username)

    def test_filtering_on_non_required_fields(self):
        # See issue #132 - filtering with all options on a non-required
        # field should exclude any results where the field is null.
        class F(FilterSet):
            author = ModelMultipleChoiceFilter(queryset=User.objects.all())

            class Meta:
                model = Article
                fields = ['author']

        published = now()
        Article.objects.create(published=published, author=self.alex)
        Article.objects.create(published=published, author=self.alex)
        Article.objects.create(published=published)

        qs = Article.objects.all()

        # Select all authors.
        authors = [
            str(user.id)
            for user in User.objects.all()
        ]
        f = F({'author': authors}, queryset=qs)

        # The results should not include anonymous articles
        self.assertEqual(
            set(f.qs),
            set(Article.objects.exclude(author__isnull=True)),
        )


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

    def test_filtering_with_single_lookup_expr(self):
        class F(FilterSet):
            price = NumberFilter(lookup_expr='lt')

            class Meta:
                model = Book
                fields = ['price']

        f = F({'price': 16}, queryset=Book.objects.all().order_by('title'))
        self.assertQuerysetEqual(
            f.qs, ['Ender\'s Game', 'Rainbow Six'], lambda o: o.title)

    def test_filtering_with_single_lookup_expr_dictionary(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = {'price': ['lt']}

        f = F({'price__lt': 16}, queryset=Book.objects.all().order_by('title'))
        self.assertQuerysetEqual(
            f.qs, ['Ender\'s Game', 'Rainbow Six'], lambda o: o.title)

    def test_filtering_with_multiple_lookup_exprs(self):
        class F(FilterSet):
            price = NumberFilter(lookup_expr=['lt', 'gt'])

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
            price = NumberFilter(lookup_expr=['lt', 'gt', 'exact'])

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
        Book.objects.create(title="Refund", price='-10.0',
                            average_rating=5.0)
        Book.objects.create(title="Free Book", price='0.0',
                            average_rating=0.0)

    def test_filtering(self):
        class F(FilterSet):
            price = RangeFilter()

            class Meta:
                model = Book
                fields = ['price']

        qs = Book.objects.all().order_by('title')
        f = F(queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Free Book', 'Rainbow Six', 'Refund', 'Snowcrash'],
                                 lambda o: o.title)
        f = F({'price_0': '5', 'price_1': '15'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Rainbow Six'],
                                 lambda o: o.title)

        f = F({'price_0': '11'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Rainbow Six', 'Snowcrash'],
                                 lambda o: o.title)
        f = F({'price_1': '19'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Free Book', 'Rainbow Six', 'Refund'],
                                 lambda o: o.title)

        f = F({'price_0': '0', 'price_1': '12'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Free Book'],
                                 lambda o: o.title)
        f = F({'price_0': '-11', 'price_1': '0'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Free Book', 'Refund'],
                                 lambda o: o.title)
        f = F({'price_0': '0', 'price_1': '0'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Free Book'],
                                 lambda o: o.title)


# TODO:
# year & month filtering could be better. The problem is that the test dates
# are relative to today, which is always changing. So, two_weeks_ago is not a
# valid date for 'this month' during the first half of the month, but is during
# the second half. Similary, five_days_ago is not during 'this year' when the
# tests are ran on January 1. All we can test is what is absolutely never valid
# eg, a date from two_years_ago is never a valid date for 'this year'.
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

        # assert what is NOT valid for now.
        # self.assertQuerysetEqual(f.qs, [1, 3, 4, 5], lambda o: o.pk, False)
        self.assertNotIn(2, f.qs.values_list('pk', flat=True))

    def test_filtering_for_month(self):
        class F(FilterSet):
            date = DateRangeFilter()

            class Meta:
                model = Comment
                fields = ['date']

        f = F({'date': '3'})  # this month

        # assert what is NOT valid for now.
        # self.assertQuerysetEqual(f.qs, [1, 3, 4], lambda o: o.pk, False)
        self.assertNotIn(2, f.qs.values_list('pk', flat=True))
        self.assertNotIn(5, f.qs.values_list('pk', flat=True))

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


class DateFromToRangeFilterTests(TestCase):

    def test_filtering(self):
        adam = User.objects.create(username='adam')
        kwargs = {'text': 'test', 'author': adam, 'time': '10:00'}
        Comment.objects.create(date=datetime.date(2016, 1, 1), **kwargs)
        Comment.objects.create(date=datetime.date(2016, 1, 2), **kwargs)
        Comment.objects.create(date=datetime.date(2016, 1, 3), **kwargs)
        Comment.objects.create(date=datetime.date(2016, 1, 3), **kwargs)

        class F(FilterSet):
            published = DateFromToRangeFilter(name='date')

            class Meta:
                model = Comment
                fields = ['date']

        results = F(data={
            'published_0': '2016-01-02',
            'published_1': '2016-01-03'})
        self.assertEqual(len(results.qs), 3)

    def test_filtering_ignores_time(self):
        tz = timezone.get_current_timezone()
        Article.objects.create(
            published=datetime.datetime(2016, 1, 1, 10, 0, tzinfo=tz))
        Article.objects.create(
            published=datetime.datetime(2016, 1, 2, 12, 45, tzinfo=tz))
        Article.objects.create(
            published=datetime.datetime(2016, 1, 3, 18, 15, tzinfo=tz))
        Article.objects.create(
            published=datetime.datetime(2016, 1, 3, 19, 30, tzinfo=tz))

        class F(FilterSet):
            published = DateFromToRangeFilter()

            class Meta:
                model = Article
                fields = ['published']

        results = F(data={
            'published_0': '2016-01-02',
            'published_1': '2016-01-03'})
        self.assertEqual(len(results.qs), 3)


class DateTimeFromToRangeFilterTests(TestCase):

    def test_filtering(self):
        tz = timezone.get_current_timezone()
        Article.objects.create(
            published=datetime.datetime(2016, 1, 1, 10, 0, tzinfo=tz))
        Article.objects.create(
            published=datetime.datetime(2016, 1, 2, 12, 45, tzinfo=tz))
        Article.objects.create(
            published=datetime.datetime(2016, 1, 3, 18, 15, tzinfo=tz))
        Article.objects.create(
            published=datetime.datetime(2016, 1, 3, 19, 30, tzinfo=tz))

        class F(FilterSet):
            published = DateTimeFromToRangeFilter()

            class Meta:
                model = Article
                fields = ['published']

        results = F(data={
            'published_0': '2016-01-02 10:00',
            'published_1': '2016-01-03 19:00'})
        self.assertEqual(len(results.qs), 2)


class TimeRangeFilterTests(TestCase):

    def test_filtering(self):
        adam = User.objects.create(username='adam')
        kwargs = {
            'text': 'test', 'author': adam, 'date': datetime.date.today()}
        Comment.objects.create(time='7:30', **kwargs)
        Comment.objects.create(time='8:00', **kwargs)
        Comment.objects.create(time='9:30', **kwargs)
        Comment.objects.create(time='11:00', **kwargs)

        class F(FilterSet):
            time = TimeRangeFilter()

            class Meta:
                model = Comment
                fields = ['time']

        results = F(data={
            'time_0': '8:00',
            'time_1': '10:00'})
        self.assertEqual(len(results.qs), 2)


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
        self.assertEqual(list(F({'username': 'alex'}).qs),
                         [User.objects.get(username='alex')])
        self.assertEqual(list(F({'username': 'jose'}).qs),
                         list())

    def test_filtering_without_strict(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

        class F(FilterSet):
            username = AllValuesFilter()

            class Meta:
                model = User
                fields = ['username']
                strict = False

        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': 'alex'}).qs),
                         [User.objects.get(username='alex')])
        self.assertEqual(list(F({'username': 'jose'}).qs),
                         list(User.objects.all()))


class AllValuesMultipleFilterTests(TestCase):

    def test_filtering(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

        class F(FilterSet):
            username = AllValuesMultipleFilter()

            class Meta:
                model = User
                fields = ['username']

        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': ['alex']}).qs),
                         [User.objects.get(username='alex')])
        self.assertEqual(list(F({'username': ['alex', 'jacob']}).qs),
                         list(User.objects.filter(username__in=['alex', 'jacob'])))
        self.assertEqual(list(F({'username': ['jose']}).qs),
                         list())


class FilterMethodTests(TestCase):

    def setUp(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

    def test_filtering(self):
        class F(FilterSet):
            username = CharFilter(method='filter_username')

            class Meta:
                model = User
                fields = ['username']

            def filter_username(self, queryset, name, value):
                return queryset.filter(**{name: value})

        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': 'alex'}).qs),
                         [User.objects.get(username='alex')])
        self.assertEqual(list(F({'username': 'jose'}).qs),
                         list())

    def test_filtering_callable(self):
        def filter_username(queryset, name, value):
            return queryset.filter(**{name: value})

        class F(FilterSet):
            username = CharFilter(method=filter_username)

            class Meta:
                model = User
                fields = ['username']

        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': 'alex'}).qs),
                         [User.objects.get(username='alex')])
        self.assertEqual(list(F({'username': 'jose'}).qs),
                         list())


class O2ORelationshipTests(TestCase):

    def setUp(self):
        a1 = Account.objects.create(
            name='account1', in_good_standing=False, friendly=False)
        a2 = Account.objects.create(
            name='account2', in_good_standing=True, friendly=True)
        a3 = Account.objects.create(
            name='account3', in_good_standing=True, friendly=False)
        a4 = Account.objects.create(
            name='account4', in_good_standing=False, friendly=True)
        Profile.objects.create(account=a1, likes_coffee=True, likes_tea=False)
        Profile.objects.create(account=a2, likes_coffee=False, likes_tea=True)
        Profile.objects.create(account=a3, likes_coffee=True, likes_tea=True)
        Profile.objects.create(account=a4, likes_coffee=False, likes_tea=False)

    def test_o2o_relation(self):

        class F(FilterSet):
            class Meta:
                model = Profile
                fields = ('account',)

        f = F()
        self.assertEqual(f.qs.count(), 4)

        f = F({'account': 1})
        self.assertEqual(f.qs.count(), 1)
        self.assertQuerysetEqual(f.qs, [1], lambda o: o.pk)

    def test_o2o_relation_dictionary(self):

        class F(FilterSet):
            class Meta:
                model = Profile
                fields = {'account': ['exact'], }

        f = F()
        self.assertEqual(f.qs.count(), 4)

        f = F({'account': 1})
        self.assertEqual(f.qs.count(), 1)
        self.assertQuerysetEqual(f.qs, [1], lambda o: o.pk)

    def test_reverse_o2o_relation(self):
        class F(FilterSet):
            class Meta:
                model = Account
                fields = ('profile',)

        f = F()
        self.assertEqual(f.qs.count(), 4)

        f = F({'profile': 1})
        self.assertEqual(f.qs.count(), 1)
        self.assertQuerysetEqual(f.qs, [1], lambda o: o.pk)

    def test_o2o_relation_attribute(self):
        class F(FilterSet):
            class Meta:
                model = Profile
                fields = ('account__in_good_standing',)

        f = F()
        self.assertEqual(f.qs.count(), 4)

        f = F({'account__in_good_standing': '2'})
        self.assertEqual(f.qs.count(), 2)
        self.assertQuerysetEqual(f.qs, [2, 3], lambda o: o.pk, False)

    def test_o2o_relation_attribute2(self):
        class F(FilterSet):
            class Meta:
                model = Profile
                fields = ('account__in_good_standing', 'account__friendly',)

        f = F()
        self.assertEqual(f.qs.count(), 4)

        f = F({'account__in_good_standing': '2', 'account__friendly': '2'})
        self.assertEqual(f.qs.count(), 1)
        self.assertQuerysetEqual(f.qs, [2], lambda o: o.pk)

    def test_reverse_o2o_relation_attribute(self):
        class F(FilterSet):
            class Meta:
                model = Account
                fields = ('profile__likes_coffee',)

        f = F()
        self.assertEqual(f.qs.count(), 4)

        f = F({'profile__likes_coffee': '2'})
        self.assertEqual(f.qs.count(), 2)
        self.assertQuerysetEqual(f.qs, [1, 3], lambda o: o.pk, False)

    def test_reverse_o2o_relation_attribute2(self):
        class F(FilterSet):
            class Meta:
                model = Account
                fields = ('profile__likes_coffee', 'profile__likes_tea')

        f = F()
        self.assertEqual(f.qs.count(), 4)

        f = F({'profile__likes_coffee': '2', 'profile__likes_tea': '2'})
        self.assertEqual(f.qs.count(), 1)
        self.assertQuerysetEqual(f.qs, [3], lambda o: o.pk)


class FKRelationshipTests(TestCase):

    def test_fk_relation(self):
        company1 = Company.objects.create(name='company1')
        company2 = Company.objects.create(name='company2')
        Location.objects.create(
            company=company1, open_days="some", zip_code="90210")
        Location.objects.create(
            company=company2, open_days="WEEKEND", zip_code="11111")
        Location.objects.create(
            company=company1, open_days="monday", zip_code="12345")

        class F(FilterSet):
            class Meta:
                model = Location
                fields = ('company',)

        f = F()
        self.assertEqual(f.qs.count(), 3)

        f = F({'company': 1})
        self.assertEqual(f.qs.count(), 2)
        self.assertQuerysetEqual(f.qs, [1, 3], lambda o: o.pk, False)

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

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['comments']

        qs = User.objects.all()
        f = F({'comments': [2]}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

        class F(FilterSet):
            comments = AllValuesFilter()

            class Meta:
                model = User
                fields = ['comments']

        f = F({'comments': 2}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

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

    @unittest.skip('todo - need correct models')
    def test_fk_relation_multiple_attributes(self):
        pass

    @unittest.expectedFailure
    def test_reverse_fk_relation_multiple_attributes(self):
        company = Company.objects.create(name='company')
        Location.objects.create(
            company=company, open_days="some", zip_code="90210")
        Location.objects.create(
            company=company, open_days="WEEKEND", zip_code="11111")

        class F(FilterSet):
            class Meta:
                model = Company
                fields = ('locations__zip_code', 'locations__open_days')

        f = F({'locations__zip_code': '90210',
               'locations__open_days': 'WEEKEND'})
        self.assertEqual(f.qs.count(), 0)


class M2MRelationshipTests(TestCase):

    def setUp(self):
        alex = User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=1)
        aaron = User.objects.create(username='aaron', status=1)
        b1 = Book.objects.create(title="Ender's Game", price='1.00',
                                 average_rating=3.0)
        b2 = Book.objects.create(title="Rainbow Six", price='2.00',
                                 average_rating=4.0)
        b3 = Book.objects.create(title="Snowcrash", price='1.00',
                                 average_rating=4.0)
        Book.objects.create(title="Stranger in a Strage Land", price='2.00',
                            average_rating=3.0)
        alex.favorite_books = [b1, b2]
        aaron.favorite_books = [b1, b3]

    def test_m2m_relation(self):
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

    def test_reverse_m2m_relation(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ['lovers']

        qs = Book.objects.all().order_by('title')
        f = F({'lovers': [1]}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ["Ender's Game", "Rainbow Six"], lambda o: o.title)

        class F(FilterSet):
            lovers = AllValuesFilter()

            class Meta:
                model = Book
                fields = ['lovers']

        f = F({'lovers': 1}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ["Ender's Game", "Rainbow Six"], lambda o: o.title)

    def test_m2m_relation_attribute(self):
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

    @unittest.expectedFailure
    def test_m2m_relation_multiple_attributes(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['favorite_books__price',
                          'favorite_books__average_rating']

        qs = User.objects.all().order_by('username')
        f = F({'favorite_books__price': "1.00",
               'favorite_books__average_rating': 4.0},
              queryset=qs)
        self.assertQuerysetEqual(f.qs, ['aaron'], lambda o: o.username)

        f = F({'favorite_books__price': "3.00",
               'favorite_books__average_rating': 4.0},
              queryset=qs)
        self.assertQuerysetEqual(f.qs, [], lambda o: o.username)

    @unittest.expectedFailure
    def test_reverse_m2m_relation_multiple_attributes(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ['lovers__status', 'lovers__username']

        qs = Book.objects.all().order_by('title')
        f = F({'lovers__status': 1, 'lovers__username': "alex"}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ["Ender's Game", "Rainbow Six"], lambda o: o.title)

        f = F({'lovers__status': 1, 'lovers__username': 'jacob'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [], lambda o: o.title)

    @unittest.skip('todo')
    def test_fk_relation_on_m2m_relation(self):
        pass

    @unittest.skip('todo')
    def test_fk_relation_attribute_on_m2m_relation(self):
        pass


class SymmetricalSelfReferentialRelationshipTests(TestCase):

    def setUp(self):
        n1 = Node.objects.create(name='one')
        n2 = Node.objects.create(name='two')
        n3 = Node.objects.create(name='three')
        n4 = Node.objects.create(name='four')
        n1.adjacents.add(n2)
        n2.adjacents.add(n3)
        n2.adjacents.add(n4)
        n4.adjacents.add(n1)

    def test_relation(self):
        class F(FilterSet):
            class Meta:
                model = Node
                fields = ['adjacents']

        qs = Node.objects.all().order_by('pk')
        f = F({'adjacents': ['1']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [2, 4], lambda o: o.pk)


class NonSymmetricalSelfReferentialRelationshipTests(TestCase):

    def setUp(self):
        n1 = DirectedNode.objects.create(name='one')
        n2 = DirectedNode.objects.create(name='two')
        n3 = DirectedNode.objects.create(name='three')
        n4 = DirectedNode.objects.create(name='four')
        n1.outbound_nodes.add(n2)
        n2.outbound_nodes.add(n3)
        n2.outbound_nodes.add(n4)
        n4.outbound_nodes.add(n1)

    def test_forward_relation(self):
        class F(FilterSet):
            class Meta:
                model = DirectedNode
                fields = ['outbound_nodes']

        qs = DirectedNode.objects.all().order_by('pk')
        f = F({'outbound_nodes': ['1']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [4], lambda o: o.pk)

    def test_reverse_relation(self):
        class F(FilterSet):
            class Meta:
                model = DirectedNode
                fields = ['inbound_nodes']

        qs = DirectedNode.objects.all().order_by('pk')
        f = F({'inbound_nodes': ['1']}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [2], lambda o: o.pk)


# use naive datetimes, as pytz is required to perform
# date lookups when timezones are involved.
@override_settings(USE_TZ=False)
@unittest.skipIf(django.VERSION < (1, 9), "version does not support transformed lookup expressions")
class TransformedQueryExpressionFilterTests(TestCase):

    def test_filtering(self):
        now_dt = datetime.datetime.now()
        after_5pm = now_dt.replace(hour=18)
        before_5pm = now_dt.replace(hour=16)

        u = User.objects.create(username='alex')
        a = Article.objects.create(author=u, published=after_5pm)
        Article.objects.create(author=u, published=before_5pm)

        class F(FilterSet):
            class Meta:
                model = Article
                fields = {'published': ['hour__gte']}

        qs = Article.objects.all()
        f = F({'published__hour__gte': 17}, queryset=qs)
        self.assertEqual(len(f.qs), 1)
        self.assertQuerysetEqual(f.qs, [a.pk], lambda o: o.pk)


# use naive datetimes, as pytz is required to perform
# date lookups when timezones are involved.
@override_settings(USE_TZ=False)
class CSVFilterTests(TestCase):

    def setUp(self):
        u1 = User.objects.create(username='alex', status=1)
        u2 = User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        now_dt = datetime.datetime.now()
        after_5pm = now_dt.replace(hour=18)
        before_5pm = now_dt.replace(hour=16)

        Article.objects.create(author=u1, published=after_5pm)
        Article.objects.create(author=u2, published=after_5pm)
        Article.objects.create(author=u1, published=before_5pm)
        Article.objects.create(author=u2, published=before_5pm)

        class UserFilter(FilterSet):
            class Meta:
                model = User
                fields = {
                    'username': ['in'],
                    'status': ['in'],
                }

        class ArticleFilter(FilterSet):
            class Meta:
                model = Article
                fields = {
                    'author': ['in'],
                    'published': ['in'],
                }

        self.user_filter = UserFilter
        self.article_filter = ArticleFilter

        self.after_5pm = after_5pm.strftime('%Y-%m-%d %H:%M:%S.%f')
        self.before_5pm = before_5pm.strftime('%Y-%m-%d %H:%M:%S.%f')

    def test_numeric_filtering(self):
        F = self.user_filter

        qs = User.objects.all()
        f = F(queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'status__in': ''}, queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'status__in': ','}, queryset=qs)
        self.assertEqual(f.qs.count(), 0)

        f = F({'status__in': '0'}, queryset=qs)
        self.assertEqual(f.qs.count(), 1)

        f = F({'status__in': '0,2'}, queryset=qs)
        self.assertEqual(f.qs.count(), 3)

        f = F({'status__in': '0,,1'}, queryset=qs)
        self.assertEqual(f.qs.count(), 2)

        f = F({'status__in': '2'}, queryset=qs)
        self.assertEqual(f.qs.count(), 2)

    def test_string_filtering(self):
        F = self.user_filter

        qs = User.objects.all()
        f = F(queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'username__in': ''}, queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'username__in': ','}, queryset=qs)
        self.assertEqual(f.qs.count(), 0)

        f = F({'username__in': 'alex'}, queryset=qs)
        self.assertEqual(f.qs.count(), 1)

        f = F({'username__in': 'alex,aaron'}, queryset=qs)
        self.assertEqual(f.qs.count(), 2)

        f = F({'username__in': 'alex,,aaron'}, queryset=qs)
        self.assertEqual(f.qs.count(), 2)

        f = F({'username__in': 'alex,'}, queryset=qs)
        self.assertEqual(f.qs.count(), 1)

    def test_datetime_filtering(self):
        F = self.article_filter
        after = self.after_5pm
        before = self.before_5pm

        qs = Article.objects.all()
        f = F(queryset=qs)
        self.assertEqual(len(f.qs), 4)
        self.assertEqual(f.qs.count(), 4)

        f = F({'published__in': ''}, queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'published__in': ','}, queryset=qs)
        self.assertEqual(f.qs.count(), 0)

        f = F({'published__in': '%s' % (after, )}, queryset=qs)
        self.assertEqual(f.qs.count(), 2)

        f = F({'published__in': '%s,%s' % (after, before, )}, queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'published__in': '%s,,%s' % (after, before, )}, queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'published__in': '%s,' % (after, )}, queryset=qs)
        self.assertEqual(f.qs.count(), 2)

    def test_related_filtering(self):
        F = self.article_filter

        qs = Article.objects.all()
        f = F(queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'author__in': ''}, queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'author__in': ','}, queryset=qs)
        self.assertEqual(f.qs.count(), 0)

        f = F({'author__in': '1'}, queryset=qs)
        self.assertEqual(f.qs.count(), 2)

        f = F({'author__in': '1,2'}, queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'author__in': '1,,2'}, queryset=qs)
        self.assertEqual(f.qs.count(), 4)

        f = F({'author__in': '1,'}, queryset=qs)
        self.assertEqual(f.qs.count(), 2)


class OrderingFilterTests(TestCase):

    def setUp(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

    def test_ordering(self):
        class F(FilterSet):
            o = OrderingFilter(
                fields=('username', )
            )

            class Meta:
                model = User
                fields = ['username']

        qs = User.objects.all()
        f = F({'o': 'username'}, queryset=qs)
        names = f.qs.values_list('username', flat=True)
        self.assertEqual(list(names), ['aaron', 'alex', 'carl', 'jacob'])

    def test_ordering_with_select_widget(self):
        class F(FilterSet):
            o = OrderingFilter(
                widget=forms.Select,
                fields=('username', )
            )

            class Meta:
                model = User
                fields = ['username']

        qs = User.objects.all()
        f = F({'o': 'username'}, queryset=qs)
        names = f.qs.values_list('username', flat=True)
        self.assertEqual(list(names), ['aaron', 'alex', 'carl', 'jacob'])


class MiscFilterSetTests(TestCase):

    def setUp(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

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
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status', 'username']

        qs = User.objects.all()

        f = F({'username': 'alex', 'status': '1'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

        f = F({'username': 'alex', 'status': '2'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [], lambda o: o.pk)

    def test_filter_with_initial(self):
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
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status']

        qs = User.objects.all()
        f = F(queryset=qs)
        self.assertEqual(len(f.qs), 4)
        self.assertEqual(f.qs.count(), 4)

        f = F({'status': '0'}, queryset=qs)
        self.assertEqual(len(f.qs), 1)
        self.assertEqual(f.qs.count(), 1)

        f = F({'status': '1'}, queryset=qs)
        self.assertEqual(len(f.qs), 1)
        self.assertEqual(f.qs.count(), 1)

        f = F({'status': '2'}, queryset=qs)
        self.assertEqual(len(f.qs), 2)
        self.assertEqual(f.qs.count(), 2)

    def test_invalid_field_lookup(self):
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
