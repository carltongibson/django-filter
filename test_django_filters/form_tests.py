from __future__ import absolute_import
from __future__ import unicode_literals
from django import forms
from django.utils import unittest
from django.test import TestCase
from django.utils import six
from django.utils.timezone import now
from django_filters.filterset import FilterSet
from django_filters.filters import AllValuesFilter
from django_filters.filters import CharFilter
from django_filters.filters import ChoiceFilter
from django_filters.filters import DateRangeFilter
from django_filters.filters import ModelChoiceFilter
from django_filters.filters import ModelMultipleChoiceFilter
from django_filters.filters import MultipleChoiceFilter
from django_filters.filters import RangeFilter
from django_filters.widgets import LinkWidget
from .models import User
from .models import Comment
from .models import Book
from .models import Article
from .models import STATUS_CHOICES


class FilterSetFormTests(TestCase):

    def test_form_from_empty_filterset(self):
        class F(FilterSet):
            pass

        f = F(queryset=Book.objects.all()).form
        self.assertIsInstance(f, forms.Form)

    def test_form(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ('title',)

        f = F().form
        self.assertIsInstance(f, forms.Form)
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th><label for="id_title">Title:</label></th>
            <td>
                <input type="text" name="title" id="id_title" />
            </td>
            </tr>""")

    def test_custom_form(self):
        class MyForm(forms.Form):
            def as_table(self):
                return "lol string"

        class F(FilterSet):
            class Meta:
                model = Book
                form = MyForm

        f = F().form
        self.assertIsInstance(f, forms.Form)
        self.assertEqual(six.text_type(f), 'lol string')
    
    def test_form_prefix(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ('title',)

        f = F().form
        self.assertIsNone(f.prefix)

        f = F(prefix='prefix').form
        self.assertEqual(f.prefix, 'prefix')
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th><label for="id_prefix-title">Title:</label></th>
            <td>
                <input type="text" name="prefix-title" id="id_prefix-title" />
            </td>
            </tr>""")
    
    def test_form_fields(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status']

        f = F().form
        self.assertEqual(len(f.fields), 1)
        self.assertIn('status', f.fields)
        self.assertEqual(sorted(f.fields['status'].choices),
                         sorted(STATUS_CHOICES))

    def test_form_fields_using_widget(self):
        class F(FilterSet):
            status = ChoiceFilter(widget=forms.RadioSelect,
                                  choices=STATUS_CHOICES)

            class Meta:
                model = User
                fields = ['status', 'username']

        f = F().form
        self.assertEqual(len(f.fields), 2)
        self.assertIn('status', f.fields)
        self.assertIn('username', f.fields)
        self.assertEqual(sorted(f.fields['status'].choices),
                         sorted(STATUS_CHOICES))
        self.assertIsInstance(f.fields['status'].widget, forms.RadioSelect)

    def test_form_field_with_custom_label(self):
        class F(FilterSet):
            title = CharFilter(label="Book title")

            class Meta:
                model = Book
                fields = ('title',)

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th><label for="id_title">Book title:</label></th>
            <td>
                <input type="text" name="title" id="id_title" />
            </td>
            </tr>""")

    def test_form_field_with_manual_name(self):
        class F(FilterSet):
            book_title = CharFilter(name='title')

            class Meta:
                model = Book
                fields = ('book_title',)

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th><label for="id_book_title">Book title:</label></th>
            <td>
                <input type="text" name="book_title" id="id_book_title" />
            </td>
            </tr>""")
    
    def test_form_field_with_manual_name_and_label(self):
        class F(FilterSet):
            f1 = CharFilter(name='title', label="Book title")

            class Meta:
                model = Book
                fields = ('f1',)

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th><label for="id_f1">Book title:</label></th>
            <td>
                <input type="text" name="f1" id="id_f1" />
            </td>
            </tr>""")

    def test_filter_with_initial(self):
        class F(FilterSet):
            status = ChoiceFilter(choices=STATUS_CHOICES, initial=1)

            class Meta:
                model = User
                fields = ['status']

        f = F().form['status']
        self.assertHTMLEqual(six.text_type(f), """
            <select name="status" id="id_status">
                <option value="0">Regular</option>
                <option selected="selected" value="1">Manager</option>
                <option value="2">Admin</option>
            </select>""")

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
        self.assertHTMLEqual(six.text_type(f['o']), """
            <select id="id_o" name="o">
                <option value="status">Status</option>
            </select>""")

    def test_ordering_uses_all_fields(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True

        f = F().form
        self.assertEqual(f.fields['o'].choices,
            [('username', 'Username'), ('status', 'Status')])
        self.assertHTMLEqual(six.text_type(f['o']), """
            <select id="id_o" name="o">
                <option value="username">Username</option>
                <option value="status">Status</option>
            </select>""")

    def test_ordering_uses_filter_label(self):
        class F(FilterSet):
            username = CharFilter(label='Account')

            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True
        
        f = F().form
        self.assertEqual(f.fields['o'].choices,
            [('username', 'Account'), ('status', 'Status')])

    def test_ordering_uses_implicit_filter_name(self):
        class F(FilterSet):
            account = CharFilter(name='username')

            class Meta:
                model = User
                fields = ['account', 'status']
                order_by = True
        
        f = F().form
        self.assertEqual(f.fields['o'].choices,
            [('username', 'Account'), ('status', 'Status')])
        self.assertHTMLEqual(six.text_type(f['o']), """
            <select id="id_o" name="o">
                <option value="username">Account</option>
                <option value="status">Status</option>
            </select>""")

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

        f = F().form
        self.assertNotIn('o', f.fields)
        self.assertIn('order', f.fields)
        self.assertEqual(f.fields['order'].choices, [('status', 'Status')])
        self.assertHTMLEqual(six.text_type(f['order']), """
            <select id="id_order" name="order">
                <option value="status">Status</option>
            </select>""")

    def test_ordering_with_overridden_field_name_and_using_all_fields(self):
        class F(FilterSet):
            order_by_field = 'order'

            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True

        f = F().form
        self.assertIn('order', f.fields)
        self.assertEqual(f.fields['order'].choices,
            [('username', 'Username'), ('status', 'Status')])

    def test_ordering_with_custom_display_names(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = [('status', 'Current status')]
        
        f = F().form
        self.assertEqual(
            f.fields['o'].choices, [('status', 'Current status')])
        self.assertHTMLEqual(six.text_type(f['o']), """
            <select id="id_o" name="o">
                <option value="status">Current status</option>
            </select>""")


class CharFilterTests(TestCase):

    def test_field_output(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ['title']

        f = F().form['title']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="title" id="id_title" />''')


class BooleanFilterTests(TestCase):

    def test_field_output(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['is_active']

        f = F().form['is_active']
        self.assertHTMLEqual(six.text_type(f), '''
            <select name="is_active" id="id_is_active">
                <option selected="selected" value="1">Unknown</option>
                <option value="2">Yes</option>
                <option value="3">No</option>
            </select>''')


class ChoiceFilterTests(TestCase):

    def test_field_output(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status']

        f = F().form['status']
        self.assertHTMLEqual(six.text_type(f), """
            <select name="status" id="id_status">
                <option value="0">Regular</option>
                <option value="1">Manager</option>
                <option value="2">Admin</option>
            </select>""")

    def test_field_output_with_selection(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['status']

        f = F({'status': '1'}).form['status']
        self.assertHTMLEqual(six.text_type(f), """
            <select name="status" id="id_status">
                <option value="0">Regular</option>
                <option selected="selected" value="1">Manager</option>
                <option value="2">Admin</option>
            </select>""")

    def test_field_output_with_link_widget(self):
        class F(FilterSet):
            status = ChoiceFilter(widget=LinkWidget, choices=STATUS_CHOICES)

            class Meta:
                model = User
                fields = ['status']

        f = F().form['status']
        self.assertHTMLEqual(six.text_type(f), """
            <ul id="id_status">
                <li><a href="?status=0">Regular</a></li>
                <li><a href="?status=1">Manager</a></li>
                <li><a href="?status=2">Admin</a></li>
            </ul>""")

    def test_field_output_with_link_widget_with_selection(self):
        class F(FilterSet):
            status = ChoiceFilter(widget=LinkWidget, choices=STATUS_CHOICES)

            class Meta:
                model = User
                fields = ['status']

        f = F({'status': '1'}).form['status']
        self.assertHTMLEqual(six.text_type(f), """
            <ul id="id_status">
                <li><a href="?status=0">Regular</a></li>
                <li><a class="selected" href="?status=1">Manager</a></li>
                <li><a href="?status=2">Admin</a></li>
            </ul>""")


class MultipleChoiceFilterTests(TestCase):

    def test_field_output(self):
        class F(FilterSet):
            status = MultipleChoiceFilter(choices=STATUS_CHOICES)

            class Meta:
                model = User
                fields = ['status']

        f = F().form['status']
        self.assertHTMLEqual(six.text_type(f), """
            <select multiple="multiple" name="status" id="id_status">
                <option value="0">Regular</option>
                <option value="1">Manager</option>
                <option value="2">Admin</option>
            </select>""")


class DateFilterTests(TestCase):

    def test_field_output(self):
        class F(FilterSet):
            class Meta:
                model = Comment
                fields = ['date']

        f = F().form['date']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="date" id="id_date" />''')


class DateTimeFilterTests(TestCase):

    def test_field_output(self):
        class F(FilterSet):
            class Meta:
                model = Article
                fields = ['published']

        f = F().form['published']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="published" id="id_published" />''')


class TimeFilterTests(TestCase):

    def test_field_output(self):
        class F(FilterSet):
            class Meta:
                model = Comment
                fields = ['time']

        f = F().form['time']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="time" id="id_time" />''')


class ModelChoiceFilterTests(TestCase):
    
    def test_field_output(self):
        class F(FilterSet):
            class Meta:
                model = Comment
                fields = ['author']

        f = F().form['author']
        self.assertHTMLEqual(six.text_type(f), """
            <select name="author" id="id_author">
                <option selected="selected" value="">---------</option>
            </select>""")

    def test_field_output_with_exising_objects(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

        class F(FilterSet):
            class Meta:
                model = Comment
                fields = ['author']

        f = F().form['author']
        self.assertHTMLEqual(six.text_type(f), """
            <select name="author" id="id_author">
                <option selected="selected" value="">---------</option>
                <option value="1">alex</option>
                <option value="2">jacob</option>
                <option value="3">aaron</option>
            </select>""")

    def test_field_output_with_link_widget(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

        class F(FilterSet):
            author = ModelChoiceFilter(
                widget=LinkWidget, queryset=User.objects.all())

            class Meta:
                model = Comment
                fields = ['author']

        f = F().form['author']
        self.assertHTMLEqual(six.text_type(f), """
            <ul id="id_author">
                <li><a class="selected" href="?author=">All</a></li>
                <li><a href="?author=1">alex</a></li>
                <li><a href="?author=2">jacob</a></li>
                <li><a href="?author=3">aaron</a></li>
            </ul>""")


class ModelMultipleChoiceFilterTests(TestCase):
    
    def test_field_output(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['favorite_books']

        f = F().form['favorite_books']
        self.assertHTMLEqual(six.text_type(f), """
            <select multiple="multiple"
                    name="favorite_books"
                    id="id_favorite_books" />""")

    def test_field_output_with_exising_objects(self):
        Book.objects.create(
            title="Ender's Game", price='1.00', average_rating=3.0)
        Book.objects.create(
            title="Rainbow Six", price='1.00', average_rating=3.0)
        Book.objects.create(
            title="Snowcrash", price='1.00', average_rating=3.0)

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['favorite_books']

        f = F().form['favorite_books']
        self.assertHTMLEqual(six.text_type(f), """
            <select multiple="multiple"
                    name="favorite_books" id="id_favorite_books">
                <option value="1">Ender&39;s Game</option>
                <option value="2">Rainbow Six</option>
                <option value="3">Snowcrash</option>
            </select>""")

    def test_field_output_with_link_widget(self):
        Book.objects.create(
            title="Ender's Game", price='1.00', average_rating=3.0)
        Book.objects.create(
            title="Rainbow Six", price='1.00', average_rating=3.0)
        Book.objects.create(
            title="Snowcrash", price='1.00', average_rating=3.0)

        class F(FilterSet):
            favorite_books = ModelMultipleChoiceFilter(
                widget=LinkWidget, queryset=Book.objects.all())

            class Meta:
                model = User
                fields = ['favorite_books']

        f = F().form['favorite_books']
        self.assertHTMLEqual(six.text_type(f), """
            <ul id="id_favorite_books">
                <li><a href="?favorite_books=1">Ender's Game</a></li>
                <li><a href="?favorite_books=2">Rainbow Six</a></li>
                <li><a href="?favorite_books=3">Snowcrash</a></li>
            </ul>""")


class NumberFilterTests(TestCase):
    
    def test_field_output(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ['price']

        f = F().form['price']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="price" id="id_price" />''')


class RangeFilterTests(TestCase):

    def test_field_output(self):
        class F(FilterSet):
            price = RangeFilter()

            class Meta:
                model = Book
                fields = ['price']

        f = F().form['price']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="price_0" id="id_price_0" />
            -
            <input type="text" name="price_1" id="id_price_1" />''')


class DateRangeFilterTests(TestCase):

    def test_field_output(self):
        class F(FilterSet):
            date = DateRangeFilter()

            class Meta:
                model = Comment
                fields = ['date']

        f = F().form['date']
        self.assertHTMLEqual(six.text_type(f), """
            <select name="date" id="id_date">
                <option selected="selected" value="">Any Date</option>
                <option value="1">Today</option>
                <option value="2">Past 7 days</option>
                <option value="3">This month</option>
                <option value="4">This year</option>
            </select>""")

    def test_field_output_with_link_widget(self):
        class F(FilterSet):
            date = DateRangeFilter(widget=LinkWidget)

            class Meta:
                model = Comment
                fields = ['date']

        f = F()
        self.assertHTMLEqual(six.text_type(f.form), """
            <tr><th><label for="id_date">Date:</label></th>
            <td>
                <ul id="id_date">
                    <li><a class="selected" href="?date=">Any Date</a></li>
                    <li><a href="?date=1">Today</a></li>
                    <li><a href="?date=2">Past 7 days</a></li>
                    <li><a href="?date=3">This month</a></li>
                    <li><a href="?date=4">This year</a></li>
                </ul>
            </td>
            </tr>""")


class AllValuesFilterTests(TestCase):

    def setUp(self):
        User.objects.create(username='alex')
        User.objects.create(username='jacob')
        User.objects.create(username='aaron')

    def test_field_output(self):
        class F(FilterSet):
            username = AllValuesFilter()

            class Meta:
                model = User
                fields = ['username']

        f = F().form['username']
        self.assertHTMLEqual(six.text_type(f), """
            <select name="username" id="id_username">
                <option value="aaron">aaron</option>
                <option value="alex">alex</option>
                <option value="jacob">jacob</option>
            </select>""")

    def test_field_output_with_link_widget(self):
        class F(FilterSet):
            username = AllValuesFilter(widget=LinkWidget)

            class Meta:
                model = User
                fields = ['username']

        f = F().form['username']
        self.assertHTMLEqual(six.text_type(f), """
            <ul id="id_username">
                <li><a href="?username=aaron">aaron</a></li>
                <li><a href="?username=alex">alex</a></li>
                <li><a href="?username=jacob">jacob</a></li>
            </ul>""")


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

    @unittest.skip('todo')
    def test_reverse_fk_relation(self):
        pass

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

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th><label for="id_author__username">Username:</label></th>
            <td>
            <input type="text" name="author__username"
                   id="id_author__username" />
            </td>
            </tr>""")

        class F(FilterSet):
            author__username = AllValuesFilter()

            class Meta:
                model = Article
                fields = ['author__username']

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr>
            <th>
                <label for="id_author__username">Author username:</label>
            </th>
            <td>
                <select name="author__username"  id="id_author__username">
                    <option value="alex">alex</option>
                    <option value="jacob">jacob</option>
                </select>
            </td>
            </tr>""")

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

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th><label for="id_comments__text">Text:</label></th>
            <td>
            <input type="text" name="comments__text"
                   id="id_comments__text" />
            </td>
            </tr>""")

        class F(FilterSet):
            comments__text = AllValuesFilter()

            class Meta:
                model = User
                fields = ['comments__text']

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr>
            <th>
                <label for="id_comments__text">Comments text:</label>
            </th>
            <td>
                <select name="comments__text"  id="id_comments__text">
                    <option value="comment 1">comment 1</option>
                    <option value="comment 2">comment 2</option>
                    <option value="comment 3">comment 3</option>
                </select>
            </td>
            </tr>""")

    @unittest.skip('todo')
    def test_m2m_relation(self):
        pass

    @unittest.skip('todo')
    def test_reverse_m2m_relation(self):
        pass

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
        alex.favorite_books = [b1, b2]
        aaron.favorite_books = [b1, b3]

        class F(FilterSet):
            class Meta:
                model = User
                fields = ['favorite_books__title']

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th><label for="id_favorite_books__title">Title:</label></th>
            <td>
            <input type="text" name="favorite_books__title"
                   id="id_favorite_books__title" />
            </td>
            </tr>""")

        class F(FilterSet):
            favorite_books__title = MultipleChoiceFilter()

            class Meta:
                model = User
                fields = ['favorite_books__title']
        
        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th>
                <label for="id_favorite_books__title">
                Favorite books title:
                </label>
            </th>
            <td>
            <select multiple="multiple" name="favorite_books__title"
                    id="id_favorite_books__title" />
            </td>
            </tr>""")

        class F(FilterSet):
            favorite_books__title = AllValuesFilter()

            class Meta:
                model = User
                fields = ['favorite_books__title']

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th>
                <label for="id_favorite_books__title">
                Favorite books title:
                </label>
            </th>
            <td>
            <select name="favorite_books__title" id="id_favorite_books__title">
                <option value="None">None</option>
                <option value="Ender's Game">Ender&39;s Game</option>
                <option value="Rainbow Six">Rainbow Six</option>
                <option value="Snowcrash">Snowcrash</option>
            </select>
            </td>
            </tr>""")

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
        alex.favorite_books = [b1, b2]
        aaron.favorite_books = [b1, b3]

        class F(FilterSet):
            class Meta:
                model = Book
                fields = ['lovers__username']
        
        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th>
                <label for="id_lovers__username">
                Username:
                </label>
            </th>
            <td>
            <input type="text" name="lovers__username"
                    id="id_lovers__username" />
            </td>
            </tr>""")

        class F(FilterSet):
            lovers__username = AllValuesFilter()

            class Meta:
                model = Book
                fields = ['lovers__username']

        f = F().form
        self.assertHTMLEqual(six.text_type(f), """
            <tr><th>
                <label for="id_lovers__username">
                Lovers username:
                </label>
            </th>
            <td>
            <select name="lovers__username" id="id_lovers__username">
                <option value="aaron">aaron</option>
                <option value="alex">alex</option>
            </select>
            </td>
            </tr>""")

    @unittest.skip('todo')
    def test_fk_relation_on_m2m_relation(self):
        pass

    @unittest.skip('todo')
    def test_fk_relation_attribute_on_m2m_relation(self):
        pass


class LookupTypesFilterTests(TestCase):

    def test_field_output_with_multiple_lookup_types(self):
        class F(FilterSet):
            title = CharFilter(lookup_type=('istartswith', 'iendswith'))

            class Meta:
                model = Book
                fields = ['title']

        f = F().form['title']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="title_0" id="id_title_0" />
            <select name="title_1" id="id_title_1">
                <option value="iendswith">iendswith</option>
                <option value="istartswith">istartswith</option>
            </select>''')

    @unittest.skip('todo')
    def test_field_output_with_multiple_labeled_lookup_types(self):
        class F(FilterSet):
            title = CharFilter(lookup_type=(
                ('istartswith', 'Ends with'),
                ('iendswith', 'Starts with'),
            ))

            class Meta:
                model = Book
                fields = ['title']

        f = F().form['title']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="title_0" id="id_title_0" />
            <select name="title_1" id="id_title_1">
                <option value="iendswith">Ends with</option>
                <option value="istartswith">Starts with</option>
            </select>''')

    def test_field_output_with_all_lookup_types(self):
        class F(FilterSet):
            title = CharFilter(lookup_type=None)

            class Meta:
                model = Book
                fields = ['title']

        f = F().form['title']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="title_0" id="id_title_0" />
            <select name="title_1" id="id_title_1">
                <option value="contains">contains</option>
                <option value="day">day</option>
                <option value="endswith">endswith</option>
                <option value="exact">exact</option>
                <option value="gt">gt</option>
                <option value="gte">gte</option>
                <option value="icontains">icontains</option>
                <option value="iendswith">iendswith</option>
                <option value="iexact">iexact</option>
                <option value="in">in</option>
                <option value="iregex">iregex</option>
                <option value="isnull">isnull</option>
                <option value="istartswith">istartswith</option>
                <option value="lt">lt</option>
                <option value="lte">lte</option>
                <option value="month">month</option>
                <option value="range">range</option>
                <option value="regex">regex</option>
                <option value="search">search</option>
                <option value="startswith">startswith</option>
                <option value="week_day">week_day</option>
                <option value="year">year</option>
            </select>''')
    
    @unittest.expectedFailure
    def test_field_output_only_shows_valid_lookup_types(self):
        class F(FilterSet):
            title = CharFilter(lookup_type=True)

            class Meta:
                model = Book
                fields = ['title']

        f = F().form['title']
        self.assertHTMLEqual(six.text_type(f), '''
            <input type="text" name="title_0" id="id_title_0" />
            <select name="title_1" id="id_title_1">
                <option value="contains">contains</option>
                <option value="endswith">endswith</option>
                <option value="exact">exact</option>
                <option value="icontains">icontains</option>
                <option value="iendswith">iendswith</option>
                <option value="iexact">iexact</option>
                <option value="in">in</option>
                <option value="iregex">iregex</option>
                <option value="isnull">isnull</option>
                <option value="istartswith">istartswith</option>
                <option value="regex">regex</option>
                <option value="search">search</option>
                <option value="startswith">startswith</option>
            </select>''')

