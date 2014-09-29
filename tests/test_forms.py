from __future__ import absolute_import
from __future__ import unicode_literals

from django import forms
from django.test import TestCase

from django_filters.filterset import FilterSet
from django_filters.filters import CharFilter
from django_filters.filters import ChoiceFilter

from .models import User
from .models import Book
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
        self.assertEqual(list(f.fields), ['title'])

    def test_custom_form(self):
        class MyForm(forms.Form):
            pass

        class F(FilterSet):
            class Meta:
                model = Book
                form = MyForm

        f = F().form
        self.assertIsInstance(f, MyForm)

    def test_form_prefix(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ('title',)

        f = F().form
        self.assertIsNone(f.prefix)

        f = F(prefix='prefix').form
        self.assertEqual(f.prefix, 'prefix')

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

    def test_form_fields_exclusion(self):
        class F(FilterSet):
            title = CharFilter(exclude=True)

            class Meta:
                model = Book
                fields = ('title',)

        f = F().form
        self.assertEqual(f.fields['title'].help_text, "This is an exclusion filter")

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
        self.assertEqual(f.fields['title'].label, "Book title")
        self.assertEqual(f['title'].label, 'Book title')

    def test_form_field_with_manual_name(self):
        class F(FilterSet):
            book_title = CharFilter(name='title')

            class Meta:
                model = Book
                fields = ('book_title',)

        f = F().form
        self.assertEqual(f.fields['book_title'].label, None)
        self.assertEqual(f['book_title'].label, 'Book title')

    def test_form_field_with_manual_name_and_label(self):
        class F(FilterSet):
            f1 = CharFilter(name='title', label="Book title")

            class Meta:
                model = Book
                fields = ('f1',)

        f = F().form
        self.assertEqual(f.fields['f1'].label, "Book title")
        self.assertEqual(f['f1'].label, 'Book title')

    def test_filter_with_initial(self):
        class F(FilterSet):
            status = ChoiceFilter(choices=STATUS_CHOICES, initial=1)

            class Meta:
                model = User
                fields = ['status']

        f = F().form
        self.assertEqual(f.fields['status'].initial, 1)

    def test_form_is_not_bound(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ('title',)

        f = F().form
        self.assertFalse(f.is_bound)
        self.assertEqual(f.data, {})

    def test_form_is_bound(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = ('title',)

        f = F({'title': 'Some book'}).form
        self.assertTrue(f.is_bound)
        self.assertEqual(f.data, {'title': 'Some book'})

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

    def test_ordering_uses_all_fields(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True

        f = F().form
        self.assertEqual(f.fields['o'].choices,
            [('username', 'Username'), ('-username', 'Username (descending)'), ('status', 'Status'), ('-status', 'Status (descending)')])

    def test_ordering_uses_filter_label(self):
        class F(FilterSet):
            username = CharFilter(label='Account')

            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = True

        f = F().form
        self.assertEqual(f.fields['o'].choices,
            [('username', 'Account'), ('-username', 'Account (descending)'), ('status', 'Status'), ('-status', 'Status (descending)')])

    def test_ordering_uses_implicit_filter_name(self):
        class F(FilterSet):
            account = CharFilter(name='username')

            class Meta:
                model = User
                fields = ['account', 'status']
                order_by = True

        f = F().form
        self.assertEqual(f.fields['o'].choices,
            [('username', 'Account'), ('-username', 'Account (descending)'), ('status', 'Status'), ('-status', 'Status (descending)')])

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
    
    def test_ordering_with_overridden_field_name_and_descending(self):
        """
        Set the `order_by_field` on the queryset and ensure that the
        field name is respected.
        """
        class F(FilterSet):
            order_by_field = 'order'

            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = ['status', '-status']

        f = F().form
        self.assertNotIn('o', f.fields)
        self.assertIn('order', f.fields)
        self.assertEqual(f.fields['order'].choices, [('status', 'Status'), ('-status', 'Status (descending)')])

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
            [('username', 'Username'), ('-username', 'Username (descending)'), ('status', 'Status'), ('-status', 'Status (descending)')])

    def test_ordering_with_custom_display_names(self):
        class F(FilterSet):
            class Meta:
                model = User
                fields = ['username', 'status']
                order_by = [('status', 'Current status')]

        f = F().form
        self.assertEqual(
            f.fields['o'].choices, [('status', 'Current status')])

