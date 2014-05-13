from __future__ import absolute_import
from __future__ import unicode_literals

import decimal

import django
from django import forms
from django.utils import unittest
from django.test import TestCase

from django_filters.widgets import RangeWidget
from django_filters.fields import RangeField
from django_filters.fields import LookupTypeField
from django_filters.fields import Lookup

def to_d(float_value):
    return decimal.Decimal('%.2f' % float_value)


class RangeFieldTests(TestCase):

    def test_field(self):
        f = RangeField()
        self.assertEqual(len(f.fields), 2)

    def test_clean(self):
        w = RangeWidget()
        f = RangeField(widget=w)

        self.assertEqual(
            f.clean(['12.34', '55']),
            slice(to_d(12.34), to_d(55)))


class LookupTypeFieldTests(TestCase):

    def test_field(self):
        inner = forms.DecimalField()
        f = LookupTypeField(inner, [('gt', 'gt'), ('lt', 'lt')])
        self.assertEqual(len(f.fields), 2)

    def test_clean(self):
        inner = forms.DecimalField()
        f = LookupTypeField(inner, [('gt', 'gt'), ('lt', 'lt')])
        self.assertEqual(
            f.clean(['12.34', 'lt']),
            Lookup(to_d(12.34), 'lt'))

    @unittest.skipIf(django.VERSION >= (1, 6),
                     'Django 1.6 uses html5 fields')
    def test_render(self):
        inner = forms.DecimalField()
        f = LookupTypeField(inner, [('gt', 'gt'), ('lt', 'lt')])
        self.assertHTMLEqual(f.widget.render('price', ''), """
            <input type="text" name="price_0" />
            <select name="price_1">
                <option value="gt">gt</option>
                <option value="lt">lt</option>
            </select>""")
        self.assertHTMLEqual(f.widget.render('price', ['abc', 'lt']), """
            <input type="text" name="price_0" value="abc" />
            <select name="price_1">
                <option value="gt">gt</option>
                <option selected="selected" value="lt">lt</option>
            </select>""")

    @unittest.skipUnless(django.VERSION >= (1, 6),
                         'Django 1.6 uses html5 fields')
    def test_render_used_html5(self):
        inner = forms.DecimalField()
        f = LookupTypeField(inner, [('gt', 'gt'), ('lt', 'lt')])
        self.assertHTMLEqual(f.widget.render('price', ''), """
            <input type="number" step="any" name="price_0" />
            <select name="price_1">
                <option value="gt">gt</option>
                <option value="lt">lt</option>
            </select>""")
        self.assertHTMLEqual(f.widget.render('price', ['abc', 'lt']), """
            <input type="number" step="any" name="price_0" value="abc" />
            <select name="price_1">
                <option value="gt">gt</option>
                <option selected="selected" value="lt">lt</option>
            </select>""")

