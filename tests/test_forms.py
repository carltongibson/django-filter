from __future__ import absolute_import
from __future__ import unicode_literals

from django import forms
from django.test import TestCase

from django_filters.filterset import FilterSet
from django_filters.filters import CharFilter
from django_filters.filters import ChoiceFilter

from .models import User, ManagerGroup
from .models import Book
from .models import STATUS_CHOICES, REGULAR, MANAGER


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
                fields = '__all__'
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

    def test_limit_choices_to(self):
        User.objects.create(username='inactive', is_active=False, status=REGULAR)
        User.objects.create(username='active', is_active=True, status=REGULAR)
        User.objects.create(username='manager', is_active=False, status=MANAGER)

        class F(FilterSet):
            class Meta:
                model = ManagerGroup
                fields = ['users', 'manager']
        f = F().form
        self.assertEqual(
            list(f.fields['users'].choices), [(2, 'active')]
        )
        self.assertEqual(
            list(f.fields['manager'].choices), [('', '---------'), (3, 'manager')]
        )
