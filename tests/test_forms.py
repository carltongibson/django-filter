from __future__ import absolute_import, unicode_literals

from django import forms
from django.test import TestCase, override_settings

from django_filters.filters import CharFilter, ChoiceFilter
from django_filters.filterset import FilterSet

from .models import MANAGER, REGULAR, STATUS_CHOICES, Book, ManagerGroup, User


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
        self.assertSequenceEqual(
            list(f.fields['status'].choices),
            (('', '---------'), ) + STATUS_CHOICES
        )

    def test_form_fields_exclusion(self):
        class F(FilterSet):
            title = CharFilter(exclude=True)

            class Meta:
                model = Book
                fields = ('title',)

        f = F().form
        self.assertEqual(f.fields['title'].label, "Exclude title")

    def test_complex_form_fields(self):
        class F(FilterSet):
            username = CharFilter(label='Filter for users with username')
            exclude_username = CharFilter(name='username', lookup_expr='iexact', exclude=True)

            class Meta:
                model = User
                fields = {
                    'status': ['exact', 'lt', 'gt'],
                    'favorite_books__title': ['iexact', 'in'],
                    'manager_of__users__username': ['exact'],
                }

        fields = F().form.fields
        self.assertEqual(fields['username'].label, 'Filter for users with username')
        self.assertEqual(fields['exclude_username'].label, 'Exclude username')
        self.assertEqual(fields['status'].label, 'Status')
        self.assertEqual(fields['status__lt'].label, 'Status is less than')
        self.assertEqual(fields['status__gt'].label, 'Status is greater than')
        self.assertEqual(fields['favorite_books__title__iexact'].label, 'Favorite books title')
        self.assertEqual(fields['favorite_books__title__in'].label, 'Favorite books title is in')
        self.assertEqual(fields['manager_of__users__username'].label, 'Manager of users username')

    def test_form_fields_using_widget(self):
        class F(FilterSet):
            status = ChoiceFilter(widget=forms.RadioSelect,
                                  choices=STATUS_CHOICES,
                                  empty_label=None)

            class Meta:
                model = User
                fields = ['status', 'username']

        f = F().form
        self.assertEqual(len(f.fields), 2)
        self.assertIn('status', f.fields)
        self.assertIn('username', f.fields)
        self.assertSequenceEqual(
            list(f.fields['status'].choices),
            STATUS_CHOICES
        )
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
        self.assertEqual(f.fields['book_title'].label, "Title")
        self.assertEqual(f['book_title'].label, "Title")

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

    def test_disabled_help_text(self):
        class F(FilterSet):
            class Meta:
                model = Book
                fields = {
                    # 'in' lookups are CSV-based, which have a `help_text`.
                    'title': ['in']
                }

        self.assertEqual(
            F().form.fields['title__in'].help_text,
            'Multiple values may be separated by commas.'
        )

        with override_settings(FILTERS_DISABLE_HELP_TEXT=True):

            self.assertEqual(
                F().form.fields['title__in'].help_text,
                ''
            )
