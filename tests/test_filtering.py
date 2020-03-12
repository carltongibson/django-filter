import contextlib
import datetime
import mock
import unittest
from operator import attrgetter

from django import forms
from django.http import QueryDict
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.timezone import make_aware, now

from django_filters.filters import (
    AllValuesFilter,
    AllValuesMultipleFilter,
    CharFilter,
    ChoiceFilter,
    DateFromToRangeFilter,
    DateRangeFilter,
    DateTimeFromToRangeFilter,
    DurationFilter,
    IsoDateTimeFromToRangeFilter,
    LookupChoiceFilter,
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    MultipleChoiceFilter,
    OrderingFilter,
    RangeFilter,
    TimeRangeFilter,
    TypedMultipleChoiceFilter
)
from django_filters.filterset import FilterSet

from .models import (
    STATUS_CHOICES,
    Account,
    Article,
    BankAccount,
    Book,
    Comment,
    Company,
    DirectedNode,
    Location,
    Node,
    Profile,
    SpacewalkRecord,
    User
)
from .utils import MockQuerySet


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

    @classmethod
    def setUpTestData(cls):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        Article.objects.create(author_id=1, published=now())
        Article.objects.create(author_id=2, published=now())
        Article.objects.create(author_id=3, published=now())
        Article.objects.create(author_id=4, published=now())
        Article.objects.create(author_id=None, published=now())

    def test_filtering(self):
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

    def test_filtering_on_empty_choice(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status']

        f = F({'status': ''})
        self.assertQuerysetEqual(f.qs,
                                 ['aaron', 'alex', 'jacob', 'carl'],
                                 lambda o: o.username, False)

    def test_filtering_on_null_choice(self):
        choices = [(u.pk, str(u)) for u in User.objects.order_by('id')]

        class F(FilterSet):
            author = ChoiceFilter(
                choices=choices,
                null_value='null',
                null_label='NULL',
            )

            class Meta:
                model = Article
                fields = ['author']

        # sanity check to make sure the filter is setup correctly
        f = F({'author': '1'})
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: str(o.author), False)

        f = F({'author': 'null'})
        self.assertQuerysetEqual(f.qs, [None], lambda o: o.author, False)


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

    def test_filtering_on_null_choice(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        Article.objects.create(author_id=1, published=now())
        Article.objects.create(author_id=2, published=now())
        Article.objects.create(author_id=3, published=now())
        Article.objects.create(author_id=4, published=now())
        Article.objects.create(author_id=None, published=now())

        choices = [(u.pk, str(u)) for u in User.objects.order_by('id')]

        class F(FilterSet):
            author = MultipleChoiceFilter(
                choices=choices,
                null_value='null',
                null_label='NULL',
            )

            class Meta:
                model = Article
                fields = ['author']

        # sanity check to make sure the filter is setup correctly
        f = F({'author': ['1']})
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: str(o.author), False)

        f = F({'author': ['null']})
        self.assertQuerysetEqual(f.qs, [None], lambda o: o.author, False)

        f = F({'author': ['1', 'null']})
        self.assertQuerysetEqual(
            f.qs, ['alex', None],
            lambda o: o.author and str(o.author),
            False)


class TypedMultipleChoiceFilterTests(TestCase):

    def test_filtering(self):
        User.objects.create(username='alex', status=1)
        User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        class F(FilterSet):
            status = TypedMultipleChoiceFilter(choices=STATUS_CHOICES, coerce=lambda x: x[0:2])

            class Meta:
                model = User
                fields = ['status']

        qs = User.objects.all().order_by('username')
        f = F(queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ['aa', 'ja', 'al', 'ca'],
            lambda o: o.username[0:2], False)

        f = F({'status': ['0']}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ['ca'], lambda o: o.username[0:2])

        f = F({'status': ['0', '1']}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ['al', 'ca'], lambda o: o.username[0:2])

        f = F({'status': ['0', '1', '2']}, queryset=qs)
        self.assertQuerysetEqual(
            f.qs, ['aa', 'al', 'ca', 'ja'], lambda o: o.username[0:2])


class DateFilterTests(TestCase):

    def test_filtering(self):
        today = now().date()
        timestamp = now().time().replace(microsecond=0)
        last_week = today - datetime.timedelta(days=7)
        check_date = str(last_week)
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
        check_time = str(fixed_time)
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
        check_dt = str(local_ten_min_ago)

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
            min_duration = DurationFilter(field_name='duration', lookup_expr='gte')
            max_duration = DurationFilter(field_name='duration', lookup_expr='lte')

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

    @override_settings(FILTERS_NULL_CHOICE_LABEL='No Author')
    def test_filtering_null(self):
        Article.objects.create(published=now())
        alex = User.objects.create(username='alex')
        Article.objects.create(author=alex, published=now())

        class F(FilterSet):
            class Meta:
                model = Article
                fields = ['author', 'name']

        qs = Article.objects.all()
        f = F({'author': 'null'}, queryset=qs)
        self.assertQuerysetEqual(f.qs, [None], lambda o: o.author, False)

    def test_callable_queryset(self):
        # Sanity check for callable queryset arguments.
        # Ensure that nothing is improperly cached
        User.objects.create(username='alex')
        jacob = User.objects.create(username='jacob')
        aaron = User.objects.create(username='aaron')

        def users(request):
            return User.objects.filter(pk__lt=request.user.pk)

        class F(FilterSet):
            author = ModelChoiceFilter(field_name='author', queryset=users)

            class Meta:
                model = Comment
                fields = ['author']

        qs = Comment.objects.all()
        request = mock.Mock()

        request.user = jacob
        f = F(queryset=qs, request=request).filters['author'].field
        self.assertQuerysetEqual(f.queryset, [1], lambda o: o.pk, False)

        request.user = aaron
        f = F(queryset=qs, request=request).filters['author'].field
        self.assertQuerysetEqual(f.queryset, [1, 2], lambda o: o.pk, False)


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
        alex.favorite_books.add(b1, b2)
        aaron.favorite_books.add(b1, b3)

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

    @override_settings(FILTERS_NULL_CHOICE_LABEL='No Favorites')
    def test_filtering_null(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['favorite_books']

        qs = User.objects.all()
        f = F({'favorite_books': ['null']}, queryset=qs)

        self.assertQuerysetEqual(f.qs, ['jacob'], lambda o: o.username)

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
                super().__init__(*args, **kwargs)
                # This filter has a limited number of choices.
                self.filters['favorite_books'].extra.update({
                    'queryset': Book.objects.filter(id__in=[1, 2])
                })

                self.filters['favorite_books'].extra['required'] = True

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
        f = F({'price_min': '5', 'price_max': '15'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Rainbow Six'],
                                 lambda o: o.title)

        f = F({'price_min': '11'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Rainbow Six', 'Snowcrash'],
                                 lambda o: o.title)
        f = F({'price_max': '19'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Free Book', 'Rainbow Six', 'Refund'],
                                 lambda o: o.title)

        f = F({'price_min': '0', 'price_max': '12'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Free Book'],
                                 lambda o: o.title)
        f = F({'price_min': '-11', 'price_max': '0'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Free Book', 'Refund'],
                                 lambda o: o.title)
        f = F({'price_min': '0', 'price_max': '0'}, queryset=qs)
        self.assertQuerysetEqual(f.qs,
                                 ['Free Book'],
                                 lambda o: o.title)


class DateRangeFilterTests(TestCase):

    class CommentFilter(FilterSet):
        date = DateRangeFilter()

        class Meta:
            model = Comment
            fields = ['date']

    @contextlib.contextmanager
    def relative_to(self, today):
        today = make_aware(today)
        yesterday = today - datetime.timedelta(days=1)
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
        Comment.objects.create(date=yesterday, author=alex, time=time)
        Comment.objects.create(date=two_months_ago, author=alex, time=time)

        with mock.patch('django_filters.filters.now') as mock_now:
            mock_now.return_value = today
            yield

    def test_filtering_for_year(self):
        f = self.CommentFilter({'date': 'year'})
        with self.relative_to(datetime.datetime(now().year, 4, 1)):
            self.assertQuerysetEqual(f.qs, [1, 3, 4, 5, 6], lambda o: o.pk, False)

    def test_filtering_for_month(self):
        f = self.CommentFilter({'date': 'month'})
        with self.relative_to(datetime.datetime(now().year, 4, 21)):
            self.assertQuerysetEqual(f.qs, [1, 3, 4, 5], lambda o: o.pk, False)

    def test_filtering_for_week(self):
        f = self.CommentFilter({'date': 'week'})
        with self.relative_to(datetime.datetime(now().year, 1, 1)):
            self.assertQuerysetEqual(f.qs, [3, 4, 5], lambda o: o.pk, False)

    def test_filtering_for_yesterday(self):
        f = self.CommentFilter({'date': 'yesterday'})
        with self.relative_to(datetime.datetime(now().year, 1, 1)):
            self.assertQuerysetEqual(f.qs, [5], lambda o: o.pk, False)

    def test_filtering_for_today(self):
        f = self.CommentFilter({'date': 'today'})
        with self.relative_to(datetime.datetime(now().year, 1, 1)):
            self.assertQuerysetEqual(f.qs, [4], lambda o: o.pk, False)


class DateFromToRangeFilterTests(TestCase):

    def test_filtering(self):
        adam = User.objects.create(username='adam')
        kwargs = {'text': 'test', 'author': adam, 'time': '10:00'}
        Comment.objects.create(date=datetime.date(2016, 1, 1), **kwargs)
        Comment.objects.create(date=datetime.date(2016, 1, 2), **kwargs)
        Comment.objects.create(date=datetime.date(2016, 1, 3), **kwargs)
        Comment.objects.create(date=datetime.date(2016, 1, 3), **kwargs)

        class F(FilterSet):
            published = DateFromToRangeFilter(field_name='date')

            class Meta:
                model = Comment
                fields = ['date']

        results = F(data={
            'published_after': '2016-01-02',
            'published_before': '2016-01-03'})
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
            'published_after': '2016-01-02',
            'published_before': '2016-01-03'})
        self.assertEqual(len(results.qs), 3)

    @override_settings(TIME_ZONE='America/Sao_Paulo')
    def test_filtering_dst_start_midnight(self):
        tz = timezone.get_default_timezone()
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 10, 14, 23, 59)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 10, 15, 0, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 10, 15, 1, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 10, 16, 0, 0)))

        class F(FilterSet):
            published = DateFromToRangeFilter()

            class Meta:
                model = Article
                fields = ['published']

        results = F(data={
            'published_after': '2017-10-15',
            'published_before': '2017-10-15'})
        self.assertEqual(len(results.qs), 2)

    @override_settings(TIME_ZONE='America/Sao_Paulo')
    def test_filtering_dst_ends_midnight(self):
        tz = timezone.get_default_timezone()
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 2, 19, 0, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 2, 18, 23, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 2, 18, 0, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 2, 17, 15, 0)))

        class F(FilterSet):
            published = DateFromToRangeFilter()

            class Meta:
                model = Article
                fields = ['published']

        results = F(data={
            'published_after': '2017-02-18',
            'published_before': '2017-02-18'})
        self.assertEqual(len(results.qs), 2)

    @override_settings(TIME_ZONE='Europe/Paris')
    def test_filtering_dst_start(self):
        tz = timezone.get_default_timezone()
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 3, 25, 23, 59)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 3, 26, 0, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 3, 26, 2, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 3, 26, 3, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 3, 27, 0, 0)))

        class F(FilterSet):
            published = DateFromToRangeFilter()

            class Meta:
                model = Article
                fields = ['published']

        results = F(data={
            'published_after': '2017-3-26',
            'published_before': '2017-3-26'})
        self.assertEqual(len(results.qs), 3)

    @override_settings(TIME_ZONE='Europe/Paris')
    def test_filtering_dst_end(self):
        tz = timezone.get_default_timezone()
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 10, 28, 23, 59)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 10, 29, 0, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 10, 29, 2, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 10, 29, 3, 0)))
        Article.objects.create(published=tz.localize(datetime.datetime(2017, 10, 30, 0, 0)))

        class F(FilterSet):
            published = DateFromToRangeFilter()

            class Meta:
                model = Article
                fields = ['published']

        results = F(data={
            'published_after': '2017-10-29',
            'published_before': '2017-10-29'})
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
            'published_after': '2016-01-02 10:00',
            'published_before': '2016-01-03 19:00'})
        self.assertEqual(len(results.qs), 2)


@unittest.expectedFailure
class IsoDateTimeFromToRangeFilterTests(TestCase):

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
            published = IsoDateTimeFromToRangeFilter()

            class Meta:
                model = Article
                fields = ['published']

        dt = (datetime.datetime.now(tz=tz))
        results = F(data={
            'published_after': '2016-01-02T10:00:00.000000' + dt.strftime("%z"),
            'published_before': '2016-01-03T19:00:00.000000' + dt.strftime("%z")})
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
            'time_after': '8:00',
            'time_before': '10:00'})
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

        # invalid choice
        self.assertFalse(F({'username': 'jose'}).is_valid())
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

        # invalid choice
        self.assertFalse(F({'username': 'jose'}).is_valid())
        self.assertEqual(list(F({'username': 'jose'}).qs),
                         list(User.objects.all()))


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
        alex.favorite_books.add(b1, b2)
        aaron.favorite_books.add(b1, b3)

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


@override_settings(TIME_ZONE='UTC')
class TransformedQueryExpressionFilterTests(TestCase):

    def test_filtering(self):
        now_dt = now()
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


class LookupChoiceFilterTests(TestCase):

    class BookFilter(FilterSet):
        price = LookupChoiceFilter(lookup_choices=['lt', 'gt'], field_class=forms.DecimalField)

        class Meta:
            model = Book
            fields = ['price']

    @classmethod
    def setUpTestData(cls):
        Book.objects.create(title="Ender's Game", price='10.0',
                            average_rating=4.7999999999999998)
        Book.objects.create(title="Rainbow Six", price='15.0',
                            average_rating=4.5999999999999996)
        Book.objects.create(title="Snowcrash", price='20.0',
                            average_rating=4.2999999999999998)

    def test_filtering(self):
        F = self.BookFilter

        f = F({'price': '15', 'price_lookup': 'lt'})
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game'], lambda o: o.title)
        f = F({'price': '15', 'price_lookup': 'lt'})
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game'], lambda o: o.title)
        f = F({'price': '', 'price_lookup': 'lt'})
        self.assertTrue(f.is_valid())
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Rainbow Six', 'Snowcrash'],
                                 lambda o: o.title, ordered=False)
        f = F({'price': '15'})
        self.assertFalse(f.is_valid())
        self.assertQuerysetEqual(f.qs,
                                 ['Ender\'s Game', 'Rainbow Six', 'Snowcrash'],
                                 lambda o: o.title, ordered=False)

    def test_inner_field_class_validation(self):
        f = self.BookFilter({'price': 'asdf', 'price_lookup': 'lt'})
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors, {
            'price': ['Enter a number.'],
        })

    def test_lookup_choices_validation(self):
        f = self.BookFilter({'price': '1', 'price_lookup': 'asdf'})
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors, {
            'price': ['Select a valid choice. asdf is not one of the available choices.'],
        })

    def test_lookup_omitted(self):
        f = self.BookFilter({'price': '1'})
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors, {
            'price': ['Select a lookup.'],
        })


@override_settings(TIME_ZONE='UTC')
class CSVFilterTests(TestCase):

    def setUp(self):
        u1 = User.objects.create(username='alex', status=1)
        u2 = User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        now_dt = now()
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
        qs = User.objects.order_by('pk')

        cases = [
            (None, [1, 2, 3, 4]),
            (QueryDict('status__in=1&status__in=2'), [2, 3]),
            ({'status__in': ''}, [1, 2, 3, 4]),
            ({'status__in': ','}, []),
            ({'status__in': '0'}, [4]),
            ({'status__in': '0,2'}, [2, 3, 4]),
            ({'status__in': '0,,1'}, [1, 4]),
            ({'status__in': '2'}, [2, 3]),
        ]

        for params, expected in cases:
            with self.subTest(params=params, expected=expected):
                self.assertQuerysetEqual(F(params, queryset=qs).qs,
                                         expected, attrgetter('pk'))

    def test_string_filtering(self):
        F = self.user_filter
        qs = User.objects.order_by('pk')

        cases = [
            (None, [1, 2, 3, 4]),
            (QueryDict('username__in=alex&username__in=aaron'), [3]),
            ({'username__in': ''}, [1, 2, 3, 4]),
            ({'username__in': ','}, []),
            ({'username__in': 'alex'}, [1]),
            ({'username__in': 'alex,aaron'}, [1, 3]),
            ({'username__in': 'alex,,aaron'}, [1, 3]),
            ({'username__in': 'alex,'}, [1]),
        ]

        for params, expected in cases:
            with self.subTest(params=params, expected=expected):
                self.assertQuerysetEqual(F(params, queryset=qs).qs,
                                         expected, attrgetter('pk'))

    def test_datetime_filtering(self):
        F = self.article_filter
        qs = Article.objects.order_by('pk')

        after = self.after_5pm
        before = self.before_5pm

        cases = [
            (None, [1, 2, 3, 4]),
            (QueryDict('published__in=%s&published__in=%s' % (after, before)), [3, 4]),
            ({'published__in': ''}, [1, 2, 3, 4]),
            ({'published__in': ','}, []),
            ({'published__in': '%s' % (after, )}, [1, 2]),
            ({'published__in': '%s,%s' % (after, before, )}, [1, 2, 3, 4]),
            ({'published__in': '%s,,%s' % (after, before, )}, [1, 2, 3, 4]),
            ({'published__in': '%s,' % (after, )}, [1, 2]),
        ]

        for params, expected in cases:
            with self.subTest(params=params, expected=expected):
                self.assertQuerysetEqual(F(params, queryset=qs).qs,
                                         expected, attrgetter('pk'))

    def test_related_filtering(self):
        F = self.article_filter
        qs = Article.objects.order_by('pk')

        cases = [
            (None, [1, 2, 3, 4]),
            (QueryDict('author__in=1&author__in=2'), [2, 4]),
            ({'author__in': ''}, [1, 2, 3, 4]),
            ({'author__in': ','}, []),
            ({'author__in': '1'}, [1, 3]),
            ({'author__in': '1,2'}, [1, 2, 3, 4]),
            ({'author__in': '1,,2'}, [1, 2, 3, 4]),
            ({'author__in': '1,'}, [1, 3]),
        ]

        for params, expected in cases:
            with self.subTest(params=params, expected=expected):
                self.assertQuerysetEqual(F(params, queryset=qs).qs,
                                         expected, attrgetter('pk'))


@override_settings(TIME_ZONE='UTC')
class CSVRangeFilterTests(TestCase):

    class ArticleFilter(FilterSet):
        class Meta:
            model = Article
            fields = {
                'published': ['range'],
            }

    @classmethod
    def setUpTestData(cls):
        u1 = User.objects.create(username='alex', status=1)
        u2 = User.objects.create(username='jacob', status=2)
        User.objects.create(username='aaron', status=2)
        User.objects.create(username='carl', status=0)

        now_dt = now()
        after_5pm = now_dt.replace(hour=18)
        around_5pm = now_dt.replace(hour=17)
        before_5pm = now_dt.replace(hour=16)

        Article.objects.create(author=u1, published=after_5pm)
        Article.objects.create(author=u2, published=around_5pm)
        Article.objects.create(author=u1, published=around_5pm)
        Article.objects.create(author=u2, published=before_5pm)

        cls.after_5pm = after_5pm.strftime('%Y-%m-%d %H:%M:%S.%f')
        cls.around_5pm = around_5pm.strftime('%Y-%m-%d %H:%M:%S.%f')
        cls.before_5pm = before_5pm.strftime('%Y-%m-%d %H:%M:%S.%f')

    def test_filtering(self):
        F = self.ArticleFilter

        f = F()
        self.assertEqual(f.qs.count(), 4)

        # empty value is a noop
        f = F({'published__range': ''})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.qs.count(), 4)

        # empty values are interpreted as None types
        f = F({'published__range': ','})
        self.assertEqual(f.qs.count(), 0)

        f = F({'published__range': '%s' % (self.before_5pm, )})
        self.assertFalse(f.is_valid())

        f = F({'published__range': '%s,%s' % (self.before_5pm, self.around_5pm, )})
        self.assertEqual(f.qs.count(), 3)

        f = F({'published__range': '%s,,%s' % (self.before_5pm, self.after_5pm, )})
        self.assertFalse(f.is_valid())

        # empty value is interpreted as None type
        f = F({'published__range': '%s,' % (self.before_5pm, )})
        self.assertEqual(f.qs.count(), 0)


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
            account = CharFilter(field_name='username')

            class Meta:
                model = User
                fields = ['account']

        qs = MockQuerySet()
        F({'account': 'jdoe'}, queryset=qs).qs
        qs.all.return_value.filter.assert_called_with(username__exact='jdoe')

    def test_filtering_without_meta(self):
        class F(FilterSet):
            username = CharFilter()

        f = F({'username': 'alex'}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

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
        # Initial values are a form presentation option - the FilterSet should
        # not use an initial value as a default value to filter by.
        class F(FilterSet):
            status = ChoiceFilter(choices=STATUS_CHOICES, initial=1)

            class Meta:
                model = User
                fields = ['status']

        qs = User.objects.all()
        users = ['alex', 'jacob', 'aaron', 'carl']

        f = F(queryset=qs)
        self.assertQuerysetEqual(f.qs.order_by('pk'), users, lambda o: o.username)

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
