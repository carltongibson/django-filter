from __future__ import absolute_import, unicode_literals

import decimal
from datetime import datetime, time, timedelta, tzinfo

import pytz
from django import forms
from django.test import TestCase, override_settings
from django.utils import timezone

from django_filters.fields import (
    BaseCSVField,
    BaseRangeField,
    DateRangeField,
    DateTimeRangeField,
    IsoDateTimeField,
    Lookup,
    LookupTypeField,
    RangeField,
    TimeRangeField
)
from django_filters.widgets import BaseCSVWidget, CSVWidget, RangeWidget


def to_d(float_value):
    return decimal.Decimal('%.2f' % float_value)


class LookupBoolTests(TestCase):
    def test_lookup_true(self):
        self.assertTrue(Lookup(True, 'exact'))
        self.assertTrue(Lookup(1, 'exact'))
        self.assertTrue(Lookup('1', 'exact'))
        self.assertTrue(Lookup(datetime.now(), 'exact'))

    def test_lookup_false(self):
        self.assertFalse(Lookup(False, 'exact'))
        self.assertFalse(Lookup(0, 'exact'))
        self.assertFalse(Lookup('', 'exact'))
        self.assertFalse(Lookup(None, 'exact'))


class RangeFieldTests(TestCase):

    def test_field(self):
        f = RangeField()
        self.assertEqual(len(f.fields), 2)

    def test_clean(self):
        w = RangeWidget()
        f = RangeField(widget=w, required=False)

        self.assertEqual(
            f.clean(['12.34', '55']),
            slice(to_d(12.34), to_d(55)))
        self.assertIsNone(f.clean([]))


class DateRangeFieldTests(TestCase):

    def test_field(self):
        f = DateRangeField()
        self.assertEqual(len(f.fields), 2)

    @override_settings(USE_TZ=False)
    def test_clean(self):
        w = RangeWidget()
        f = DateRangeField(widget=w, required=False)
        self.assertEqual(
            f.clean(['2015-01-01', '2015-01-10']),
            slice(datetime(2015, 1, 1, 0, 0, 0),
                  datetime(2015, 1, 10, 23, 59, 59, 999999)))
        self.assertIsNone(f.clean([]))


class DateTimeRangeFieldTests(TestCase):

    def test_field(self):
        f = DateTimeRangeField()
        self.assertEqual(len(f.fields), 2)

    @override_settings(USE_TZ=False)
    def test_clean(self):
        w = RangeWidget()
        f = DateTimeRangeField(widget=w)
        self.assertEqual(
            f.clean(['2015-01-01 10:30', '2015-01-10 8:45']),
            slice(datetime(2015, 1, 1, 10, 30, 0),
                  datetime(2015, 1, 10, 8, 45, 0)))


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
        f = LookupTypeField(inner, [('gt', 'gt'), ('lt', 'lt')], required=False)
        self.assertEqual(
            f.clean(['12.34', 'lt']),
            Lookup(to_d(12.34), 'lt'))
        self.assertEqual(
            f.clean([]),
            Lookup(value=None, lookup_type='exact'))

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
    reference_str = "2015-07-19T13:34:51.759"
    reference_dt = datetime(2015, 7, 19, 13, 34, 51, 759000)
    field = IsoDateTimeField()

    def parse_input(self, value):
        return self.field.strptime(value, IsoDateTimeField.ISO_8601)

    def test_datetime_string_is_parsed(self):
        d = self.parse_input(self.reference_str)
        self.assertTrue(isinstance(d, datetime))

    def test_datetime_string_with_timezone_is_parsed(self):
        d = self.parse_input(self.reference_str + "+01:00")
        self.assertTrue(isinstance(d, datetime))

    def test_datetime_zulu(self):
        d = self.parse_input(self.reference_str + "Z")
        self.assertTrue(isinstance(d, datetime))

    @override_settings(TIME_ZONE='UTC')
    def test_datetime_timezone_awareness(self):
        utc, tokyo = pytz.timezone('UTC'), pytz.timezone('Asia/Tokyo')

        # by default, use the server timezone
        reference = utc.localize(self.reference_dt)
        parsed = self.parse_input(self.reference_str)
        self.assertIsInstance(parsed.tzinfo, tzinfo)
        self.assertEqual(parsed, reference)

        # if set, use the active timezone
        reference = tokyo.localize(self.reference_dt)
        with timezone.override(tokyo):
            parsed = self.parse_input(self.reference_str)
        self.assertIsInstance(parsed.tzinfo, tzinfo)
        self.assertEqual(parsed.tzinfo.zone, tokyo.zone)
        self.assertEqual(parsed, reference)

        # if provided, utc offset should have precedence
        reference = utc.localize(self.reference_dt - timedelta(hours=1))
        parsed = self.parse_input(self.reference_str + "+01:00")
        self.assertIsInstance(parsed.tzinfo, tzinfo)
        self.assertEqual(parsed, reference)

    @override_settings(USE_TZ=False)
    def test_datetime_timezone_naivety(self):
        reference = self.reference_dt.replace()

        parsed = self.parse_input(self.reference_str + "+01:00")
        self.assertIsNone(parsed.tzinfo)
        self.assertEqual(parsed, reference - timedelta(hours=1))

        parsed = self.parse_input(self.reference_str)
        self.assertIsNone(parsed.tzinfo)
        self.assertEqual(parsed, reference)

    def test_datetime_non_iso_format(self):
        f = IsoDateTimeField()
        parsed = f.strptime('19-07-2015T51:34:13.759', '%d-%m-%YT%S:%M:%H.%f')
        self.assertTrue(isinstance(parsed, datetime))
        self.assertEqual(parsed, self.reference_dt)

    def test_datetime_wrong_format(self):
        with self.assertRaises(ValueError):
            self.parse_input('19-07-2015T51:34:13.759')


class BaseCSVFieldTests(TestCase):
    def setUp(self):
        class DecimalCSVField(BaseCSVField, forms.DecimalField):
            pass

        self.field = DecimalCSVField()

    def test_clean(self):
        self.assertEqual(self.field.clean(None), None)
        self.assertEqual(self.field.clean(''), [])
        self.assertEqual(self.field.clean(['1']), [1])
        self.assertEqual(self.field.clean(['1', '2']), [1, 2])
        self.assertEqual(self.field.clean(['1', '2', '3']), [1, 2, 3])

    def test_validation_error(self):
        with self.assertRaises(forms.ValidationError):
            self.field.clean([''])

        with self.assertRaises(forms.ValidationError):
            self.field.clean(['a', 'b', 'c'])

    def test_derived_widget(self):
        with self.assertRaises(AssertionError) as excinfo:
            BaseCSVField(widget=RangeWidget())

        msg = str(excinfo.exception)
        self.assertIn("'BaseCSVField.widget' must be a widget class", msg)
        self.assertIn("RangeWidget", msg)

        widget = CSVWidget(attrs={'class': 'class'})
        field = BaseCSVField(widget=widget)
        self.assertIsInstance(field.widget, CSVWidget)
        self.assertEqual(field.widget.attrs, {'class': 'class'})

        field = BaseCSVField(widget=CSVWidget)
        self.assertIsInstance(field.widget, CSVWidget)

        field = BaseCSVField(widget=forms.Select)
        self.assertIsInstance(field.widget, forms.Select)
        self.assertIsInstance(field.widget, BaseCSVWidget)


class BaseRangeFieldTests(TestCase):
    def setUp(self):
        class DecimalRangeField(BaseRangeField, forms.DecimalField):
            pass

        self.field = DecimalRangeField()

    def test_clean(self):
        self.assertEqual(self.field.clean(None), None)
        self.assertEqual(self.field.clean(['1', '2']), [1, 2])

    def test_validation_error(self):
        with self.assertRaises(forms.ValidationError):
            self.field.clean('')

        with self.assertRaises(forms.ValidationError):
            self.field.clean([''])

        with self.assertRaises(forms.ValidationError):
            self.field.clean(['1'])

        with self.assertRaises(forms.ValidationError):
            self.field.clean(['1', '2', '3'])
