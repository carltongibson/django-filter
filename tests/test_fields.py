from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime, time
import decimal
import sys

if sys.version_info >= (2, 7):
    import unittest
else:  # pragma: nocover
    from django.utils import unittest  # noqa

import django
from django import forms
from django.test import TestCase

from django_filters.widgets import RangeWidget
from django_filters.fields import (
    RangeField, LookupTypeField, Lookup, DateRangeField, TimeRangeField, IsoDateTimeField)

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


class DateRangeFieldTests(TestCase):

    def test_field(self):
        f = DateRangeField()
        self.assertEqual(len(f.fields), 2)

    def test_clean(self):
        w = RangeWidget()
        f = DateRangeField(widget=w)

        self.assertEqual(
            f.clean(['2015-01-01', '2015-01-10']),
            slice(datetime(2015, 1, 1, 0, 0 , 0),
                  datetime(2015, 1, 10, 23, 59, 59, 999999)))


class TimeRangeFieldTests(TestCase):

    def test_field(self):
        f = DateRangeField()
        self.assertEqual(len(f.fields), 2)

    def test_clean(self):
        w = RangeWidget()
        f = TimeRangeField(widget=w)

        self.assertEqual(
            f.clean(['10:15', '12:30']),
            slice(time(10, 15, 0), time(12, 30, 0)))


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


class IsoDateTimeFieldTests(TestCase):

    def test_datetime_string_is_parsed(self):
        f = IsoDateTimeField()
        d = f.strptime("2015-07-19T13:34:51.759", IsoDateTimeField.ISO_8601)
        self.assertTrue(isinstance(d, datetime))

    def test_datetime_string_with_timezone_is_parsed(self):
        f = IsoDateTimeField()
        d = f.strptime("2015-07-19T13:34:51.759+01:00", IsoDateTimeField.ISO_8601)
        self.assertTrue(isinstance(d, datetime))