from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime, time, timedelta, tzinfo
import decimal

from django import forms
from django.test import TestCase, override_settings
from django.utils.timezone import make_aware, get_default_timezone

from django_filters.widgets import BaseCSVWidget, CSVWidget, RangeWidget
from django_filters.fields import (
    Lookup, LookupTypeField, BaseCSVField, BaseRangeField, RangeField,
    DateRangeField, DateTimeRangeField, TimeRangeField, IsoDateTimeField
)


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
        f = RangeField(widget=w)

        self.assertEqual(
            f.clean(['12.34', '55']),
            slice(to_d(12.34), to_d(55)))


class DateRangeFieldTests(TestCase):

    def test_field(self):
        f = DateRangeField()
        self.assertEqual(len(f.fields), 2)

    @override_settings(USE_TZ=False)
    def test_clean(self):
        w = RangeWidget()
        f = DateRangeField(widget=w)
        self.assertEqual(
            f.clean(['2015-01-01', '2015-01-10']),
            slice(datetime(2015, 1, 1, 0, 0, 0),
                  datetime(2015, 1, 10, 23, 59, 59, 999999)))


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
        f = LookupTypeField(inner, [('gt', 'gt'), ('lt', 'lt')])
        self.assertEqual(
            f.clean(['12.34', 'lt']),
            Lookup(to_d(12.34), 'lt'))

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

    def test_datetime_string_is_parsed(self):
        f = IsoDateTimeField()
        d = f.strptime(self.reference_str + "", IsoDateTimeField.ISO_8601)
        self.assertTrue(isinstance(d, datetime))

    def test_datetime_string_with_timezone_is_parsed(self):
        f = IsoDateTimeField()
        d = f.strptime(self.reference_str + "+01:00", IsoDateTimeField.ISO_8601)
        self.assertTrue(isinstance(d, datetime))

    def test_datetime_zulu(self):
        f = IsoDateTimeField()
        d = f.strptime(self.reference_str + "Z", IsoDateTimeField.ISO_8601)
        self.assertTrue(isinstance(d, datetime))

    def test_datetime_timezone_awareness(self):
        # parsed datetimes should obey USE_TZ
        f = IsoDateTimeField()
        r = make_aware(self.reference_dt, get_default_timezone())

        d = f.strptime(self.reference_str + "+01:00", IsoDateTimeField.ISO_8601)
        self.assertTrue(isinstance(d.tzinfo, tzinfo))
        self.assertEqual(d, r + r.utcoffset() - d.utcoffset())

        d = f.strptime(self.reference_str + "", IsoDateTimeField.ISO_8601)
        self.assertTrue(isinstance(d.tzinfo, tzinfo))
        self.assertEqual(d, r)

    @override_settings(USE_TZ=False)
    def test_datetime_timezone_naivety(self):
        # parsed datetimes should obey USE_TZ
        f = IsoDateTimeField()
        r = self.reference_dt.replace()

        d = f.strptime(self.reference_str + "+01:00", IsoDateTimeField.ISO_8601)
        self.assertTrue(d.tzinfo is None)
        self.assertEqual(d, r - timedelta(hours=1))

        d = f.strptime(self.reference_str + "", IsoDateTimeField.ISO_8601)
        self.assertTrue(d.tzinfo is None)
        self.assertEqual(d, r)


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

        widget = CSVWidget()
        field = BaseCSVField(widget=widget)
        self.assertIs(field.widget, widget)

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
