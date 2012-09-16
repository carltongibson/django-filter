import datetime
import os

from django import forms
from django.conf import settings
from django.test import TestCase

from django_filters import *
from django_filters.widgets import *

from django_filters.tests.models import User, Comment, Book, Restaurant, Article, STATUS_CHOICES


class GenericViewTests(TestCase):
    urls = 'django_filters.tests.test_urls'
    fixtures = ['test_data']
    template_dirs = [
        os.path.join(os.path.dirname(__file__), 'templates'),
    ]

    def setUp(self):
        self.old_template_dir = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = self.template_dirs

    def tearDown(self):
        settings.TEMPLATE_DIRS = self.old_template_dir

    def test_generic_view(self):
        response = self.client.get('/books/')
        for b in ['Ender&#39;s Game', 'Rainbox Six', 'Snowcrash']:
            self.assertContains(response, b)

class InheritanceTest(TestCase):
    def test_inheritance(self):
        class F(FilterSet):
            class Meta:
                model = Book

        class G(F):
            pass
        self.assertEqual(set(F.base_filters), set(G.base_filters))

class ModelInheritanceTest(TestCase):
    def test_abstract(self):
        class F(FilterSet):
            class Meta:
                model = Restaurant

        self.assertEquals(set(F.base_filters), set(['name', 'serves_pizza']))

        class F(FilterSet):
            class Meta:
                model = Restaurant
                fields = ['name', 'serves_pizza']

        self.assertEquals(set(F.base_filters), set(['name', 'serves_pizza']))


class DateRangeFilterTest(TestCase):
    def test_filter(self):
        a = Article.objects.create(published=datetime.datetime.today())
        class F(FilterSet):
            published = DateRangeFilter()
            class Meta:
                model = Article
        f = F({'published': '2'})
        self.assertEqual(list(f), [a])


class FilterSetForm(TestCase):
    def test_prefix(self):
        class F(FilterSet):
            class Meta:
                model = Restaurant
                fields = ['name']
        self.assert_('blah-prefix' in unicode(F(prefix='blah-prefix').form))

class AllValuesFilterTest(TestCase):
    fixtures = ['test_data']

    def test_filter(self):
        class F(FilterSet):
            username = AllValuesFilter()
            class Meta:
                model = User
                fields = ['username']
        form_html = ('<tr><th><label for="id_username">Username:</label></th>'
            '<td><select name="username" id="id_username">\n'
            '<option value="aaron">aaron</option>\n<option value="alex">alex'
            '</option>\n<option value="jacob">jacob</option>\n</select></td>'
            '</tr>')
        self.assertEqual(unicode(F().form), form_html)
        self.assertEqual(list(F().qs), list(User.objects.all()))
        self.assertEqual(list(F({'username': 'alex'})), [User.objects.get(username='alex')])
        self.assertEqual(list(F({'username': 'jose'})), list(User.objects.all()))

class InitialValueTest(TestCase):
    fixtures = ['test_data']

    def test_initial(self):
        class F(FilterSet):
            status = ChoiceFilter(choices=STATUS_CHOICES, initial=1)
            class Meta:
                model = User
                fields = ['status']
        self.assertEqual(list(F().qs), [User.objects.get(username='alex')])
        self.assertEqual(list(F({'status': 0})), list(User.objects.filter(status=0)))


class RelatedObjectTest(TestCase):
    fixtures = ['test_data']

    def test_foreignkey(self):
        class F(FilterSet):
            class Meta:
                model = Article
                fields = ['author__username']
        self.assertEqual(F.base_filters.keys(), ['author__username'])
        form_html = ('<tr><th><label for="id_author__username">Username:</label>'
            '</th><td><input type="text" name="author__username" '
            'id="id_author__username" /></td></tr>')
        self.assertEqual(str(F().form), form_html)
        self.assertEqual(F({'author__username': 'alex'}).qs.count(), 2)
        self.assertEqual(F({'author__username': 'jacob'}).qs.count(), 1)

        class F(FilterSet):
            author__username = AllValuesFilter()
            class Meta:
                model = Article
                fields = ['author__username']

        form_html = ('<tr><th><label for="id_author__username">Author  '
            'username:</label></th><td><select name="author__username" '
            'id="id_author__username">\n<option value="alex">alex</option>\n'
            '<option value="jacob">jacob</option>\n</select></td></tr>')
        self.assertEqual(str(F().form), form_html)


class MultipleChoiceFilterTest(TestCase):
    fixtures = ['test_data']

    def test_all_choices_selected(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ["status"]

        self.assertEqual(list(F({"status": [0, 1]}).qs), list(User.objects.all()))

class MultipleLookupTypesTest(TestCase):
    fixtures = ['test_data']

    def test_no_GET_params(self):
        class F(FilterSet):
            published = DateTimeFilter(lookup_type=['gt', 'lt'])
            class Meta:
                model = Article
                fields = ['published']

        self.assertEqual(list(F({}).qs), list(Article.objects.all()))


class FilterSetTest(TestCase):
    def test_base_filters(self):
        class F(FilterSet):
            class Meta:
                model = User

        self.assertEqual(F.base_filters.keys(), ['username', 'first_name',
            'last_name', 'status', 'is_active', 'favorite_books'])

        class F(FilterSet):
            class Meta:
                model = User
                exclude = ['is_active']

        self.assertEqual(F.base_filters.keys(), ['username', 'first_name',
            'last_name', 'status', 'favorite_books'])

    def test_filter_qs(self):
        alex = User.objects.get(username='alex')
        user_ids = list(User.objects.all().values_list('pk', flat=True))

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status', 'username']

        f = F(queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, user_ids, lambda o: o.pk)
        f = F({'username': 'alex'}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, [alex.pk], lambda o: o.pk)
        f = F({'status': '1'}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, [alex.pk], lambda o: o.pk)

    def test_forms(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status']

        f = F({'status': '1'}, queryset=User.objects.all())
        self.assertEqual(len(f.form.fields), 1)
        self.assertIn('status', f.form.fields)
        self.assertEqual(f.form.fields['status'].choices,
            [(0, 'Regular'), (1, 'Admin')])

        class F(FilterSet):
            status = ChoiceFilter(widget=forms.RadioSelect, choices=STATUS_CHOICES)
            class Meta:
                model = User
                fields = ['status', 'username']

        f = F({'status': '1'}, queryset=User.objects.all())

        self.assertEqual(len(f.form.fields), 2)
        self.assertIn('status', f.form.fields)
        self.assertIn('username', f.form.fields)
        self.assertEqual(f.form.fields['status'].choices,
            [(0, 'Regular'), (1, 'Admin')])
        self.assertEqual(type(f.form.fields['status'].widget), forms.RadioSelect)

    def test_char_filter(self):
        class F(FilterSet):
            username = CharFilter(action=lambda qs, value: qs.filter(**{'username__startswith': value}))
            class Meta:
                model = User
                fields = ['username']

        users = User.objects.filter(username__startswith = 'a').values_list('pk', flat=True)
        f = F({'username': 'a'}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, users, lambda o: o.pk, False)

    def test_multiple_choice_filter(self):
        class F(FilterSet):
            status = django_filters.MultipleChoiceFilter(choices=STATUS_CHOICES)
            class Meta:
                model = User
                fields = ['status']

        f = F(queryset=User.objects.all())
        self.assertIn('status', f.form.fields)
        self.assertEqual(f.form.fields['status'].choices,
            [(0, 'Regular'), (1, 'Admin')])
        self.assertEqual(type(f.form.fields['status']), forms.MultipleChoiceField)

        f = F({'status': ['0']}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, ['aaron', 'jacob'], lambda o: o.username)
        f = F({'status': ['0', '1']}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, ['alex', 'aaron', 'jacob'], lambda o: o.username)

    def test_date_time_filter(self):
        class F(FilterSet):
            class Meta:
                model = Comment
                fields = ['date', 'time']

        f = F({'date': '01/30/10'}, queryset=Comment.objects.all())
        self.assertQuerysetEqual(f.qs, [1], lambda o: o.pk)

        f = F({'time': '12:55'}, queryset=Comment.objects.all())
        self.assertQuerysetEqual(f.qs, [3], lambda o: o.pk)

    def test_fk_filter(self):
        class F(FilterSet):
            class Meta:
                model = Comment
                fields = ['author']

        f = F({'author': '2'}, queryset=Comment.objects.all())
        self.assertQuerysetEqual(f.qs, [2], lambda o: o.pk)

    def test_m2m_filter(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['favorite_books']

        f = F({'favorite_books': ['1']}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, ['alex', 'aaron'], lambda o: o.username)
        f = F({'favorite_books': ['1', '3']}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, ['alex', 'aaron'], lambda o: o.username)
        f = F({'favorite_books': ['2']}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username)

    def test_ordering(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status']
        f = F({'o': 'status'}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, ['aaron', 'jacob', 'alex'], lambda o: o.username)

        self.assertIn('o', f.form.fields)
        self.assertEqual(f.form.fields['o'].choices, [('status', u'Status')])

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True
        f = F({'o': 'username'}, queryset=User.objects.all())
        self.assertQuerysetEqual(f.qs, ['aaron', 'alex', 'jacob'], lambda o: o.username)
        self.assertIn('o', f.form.fields)
        self.assertEqual(f.form.fields['o'].choices,
            [('username', u'Username'), ('status', u'Status')])

    def test_number_filter(self):
        class F(FilterSet):
            price = NumberFilter(lookup_type='lt')
            average_rating = NumberFilter(lookup_type='gt')

            class Meta:
                model = Book
                fields = ['price', 'average_rating']

        f = F({'price': 15}, queryset=Book.objects.all())
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game'], lambda o: o.title)


        f = F({'average_rating': '4.5'}, queryset=Book.objects.all())
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game', 'Rainbox Six'], lambda o: o.title)

        class F(FilterSet):
            price = NumberFilter(lookup_type=None)

            class Meta:
                model = Book
                fields = ['price']

        f = F(queryset=Book.objects.all())
        # TODO
        self.assertEqual(str(f.form['price']), '<input type="text" name="price_0" id="id_price_0" /><select name="price_1" id="id_price_1">\n<option value="contains">contains</option>\n<option value="day">day</option>\n<option value="endswith">endswith</option>\n<option value="exact">exact</option>\n<option value="gt">gt</option>\n<option value="gte">gte</option>\n<option value="icontains">icontains</option>\n<option value="iendswith">iendswith</option>\n<option value="iexact">iexact</option>\n<option value="in">in</option>\n<option value="iregex">iregex</option>\n<option value="isnull">isnull</option>\n<option value="istartswith">istartswith</option>\n<option value="lt">lt</option>\n<option value="lte">lte</option>\n<option value="month">month</option>\n<option value="range">range</option>\n<option value="regex">regex</option>\n<option value="search">search</option>\n<option value="startswith">startswith</option>\n<option value="week_day">week_day</option>\n<option value="year">year</option>\n</select>')

        class F(FilterSet):
            price = NumberFilter(lookup_type=['lt', 'gt'])

            class Meta:
                model = Book
                fields = ['price']

        f = F(queryset=Book.objects.all())
        self.assertEqual(str(f.form['price']), '<input type="text" name="price_0" id="id_price_0" /><select name="price_1" id="id_price_1">\n<option value="gt">gt</option>\n<option value="lt">lt</option>\n</select>')

        f = F({'price_0': '15', 'price_1': 'lt'}, queryset=Book.objects.all())
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game'], lambda o: o.title)
        f = F({'price_0': '15', 'price_1': 'lt'})
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game'], lambda o: o.title)
        f = F({'price_0': '', 'price_1': 'lt'})
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game', 'Rainbox Six', 'Snowcrash'], lambda o: o.title)

    def test_range_filter(self):
        class F(FilterSet):
            price = RangeFilter()
            class Meta:
                model = Book
                fields = ['price']
        f = F(queryset=Book.objects.all())
        self.assertEqual(str(f.form['price']), '<input type="text" name="price_0" id="id_price_0" />-<input type="text" name="price_1" id="id_price_1" />')

        self.assertQuerysetEqual(f.qs, ['Ender\'s Game', 'Rainbox Six', 'Snowcrash'], lambda o: o.title)
        f = F({'price_0': '5', 'price_1': '15'}, queryset=Book.objects.all())
        self.assertQuerysetEqual(f.qs, ['Ender\'s Game', 'Rainbox Six'], lambda o: o.title)

    def test_choice_filter(self):
        class F(FilterSet):
            status = ChoiceFilter(widget=LinkWidget, choices=STATUS_CHOICES)
            class Meta:
                model = User
                fields = ['status']
        f = F()
        self.assertQuerysetEqual(f.qs, ['aaron', 'alex', 'jacob'], lambda o: o.username, False)

        self.assertEqual(str(f.form), """<tr><th><label for="id_status">Status:</label></th><td><ul id="id_status">
<li><a href="?status=0">Regular</a></li>
<li><a href="?status=1">Admin</a></li>
</ul></td></tr>""")
        f = F({'status': '1'})
        self.assertQuerysetEqual(f.qs, ['alex'], lambda o: o.username, False)
        self.assertEqual(str(f.form), """<tr><th><label for="id_status">Status:</label></th><td><ul id="id_status">
<li><a href="?status=0">Regular</a></li>
<li><a class="selected" href="?status=1">Admin</a></li>
</ul></td></tr>""")





filter_tests = """
>>> from datetime import datetime
>>> from django import forms
>>> from django.core.management import call_command
>>> from django_filters import *
>>> from django_filters.widgets import *
>>> from django_filters.tests.models import User, Comment, Book, STATUS_CHOICES

>>> call_command('loaddata', 'test_data', verbosity=0)

>>> class F(FilterSet):
...     class Meta:
...         model = User
...         fields = ['is_active']

'2' and '3' are how the field expects the data from the browser
>>> f = F({'is_active': '2'}, queryset=User.objects.all())
>>> f.qs
[<User: jacob>]
>>> f = F({'is_active': '3'}, queryset=User.objects.all())
>>> f.qs
[<User: alex>, <User: aaron>]
>>> f = F({'is_active': '1'}, queryset=User.objects.all())
>>> f.qs
[<User: alex>, <User: aaron>, <User: jacob>]

>>> class F(FilterSet):
...     date = DateRangeFilter(widget=LinkWidget)
...     class Meta:
...         model = Comment
...         fields = ['date']
>>> f = F()
>>> print f.form
<tr><th><label for="id_date">Date:</label></th><td><ul id="id_date">
<li><a class="selected" href="?date=">Any Date</a></li>
<li><a href="?date=1">Today</a></li>
<li><a href="?date=2">Past 7 days</a></li>
<li><a href="?date=3">This month</a></li>
<li><a href="?date=4">This year</a></li>
</ul></td></tr>
>>> f = F({'date': '4'})
>>> f.qs
[<Comment: alex said super awesome!>, <Comment: aaron said psycadelic!>]
>>> f = F({})
>>> print f.form
<tr><th><label for="id_date">Date:</label></th><td><ul id="id_date">
<li><a class="selected" href="?date=">Any Date</a></li>
<li><a href="?date=1">Today</a></li>
<li><a href="?date=2">Past 7 days</a></li>
<li><a href="?date=3">This month</a></li>
<li><a href="?date=4">This year</a></li>
</ul></td></tr>
>>> f.qs
[<Comment: alex said super awesome!>, <Comment: aaron said psycadelic!>, <Comment: jacob said funky fresh!>]
>>> _ = Comment.objects.create(text="Wowa", author = User.objects.get(username="alex"), date=datetime.today(), time="12:30")
>>> f = F({'date': '2'})
>>> f.qs
[<Comment: alex said Wowa>]

>>> class MyForm(forms.Form):
...     def as_table(self):
...         return "lol string"

>>> class F(FilterSet):
...     class Meta:
...         model = Comment
...         form = MyForm

>>> print F().form
lol string

>>> class F(FilterSet):
...     class Meta:
...         model = User
...         fields = ['status', 'username']

>>> print F().form
<tr><th><label for="id_status">Status:</label></th><td><select name="status" id="id_status">
<option value="0">Regular</option>
<option value="1">Admin</option>
</select></td></tr>
<tr><th><label for="id_username">Username:</label></th><td><input type="text" name="username" id="id_username" /></td></tr>

>>> class F(FilterSet):
...     class Meta:
...         model = User
...         fields = ['name']
Traceback (most recent call last):
...
TypeError: Meta.fields contains a field that isn't defined on this FilterSet

>>> class F(FilterSet):
...     class Meta:
...         model = Comment
...         fields = ['author', 'text']

>>> print F().form
<tr><th><label for="id_author">Author:</label></th><td><select name="author" id="id_author">
<option value="" selected="selected">---------</option>
<option value="1">alex</option>
<option value="2">aaron</option>
<option value="3">jacob</option>
</select></td></tr>
<tr><th><label for="id_text">Text:</label></th><td><input type="text" name="text" id="id_text" /></td></tr>

>>> class F(FilterSet):
...     class Meta:
...         model = User
...         order_by = ['username']

>>> f = F({})
>>> f.qs
[<User: alex>, <User: aaron>, <User: jacob>]

>>> class F(FilterSet):
...     price = NumberFilter(lookup_type=['lt', 'gt', 'exact'])
...     class Meta:
...         model = Book
...         fields = ['price']

>>> f = F({'price_0': '15'})
>>> f.qs
[<Book: Rainbox Six>]
"""
