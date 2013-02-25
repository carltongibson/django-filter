from __future__ import absolute_import
from __future__ import unicode_literals

from django.test import TestCase

from django_filters.widgets import RangeWidget
from django_filters.widgets import LinkWidget
from django_filters.widgets import LookupTypeWidget


class LookupTypeWidgetTests(TestCase):
    
    def test_widget_requires_field(self):
        with self.assertRaises(TypeError):
            LookupTypeWidget()


class LinkWidgetTests(TestCase):
    
    def test_widget_without_choices(self):
        w = LinkWidget()
        self.assertEqual(len(w.choices), 0)
        self.assertHTMLEqual(w.render('price', ''), """<ul />""")

    def test_widget(self):
        choices = (
            ('test-val1', 'test-label1'),
            ('test-val2', 'test-label2'),
        )
        w = LinkWidget(choices=choices)
        self.assertEqual(len(w.choices), 2)
        self.assertHTMLEqual(w.render('price', ''), """
            <ul>
                <li><a href="?price=test-val1">test-label1</a></li>
                <li><a href="?price=test-val2">test-label2</a></li>
            </ul>""")

        self.assertHTMLEqual(w.render('price', 'test-val1'), """
            <ul>
                <li><a class="selected"
                       href="?price=test-val1">test-label1</a></li>
                <li><a href="?price=test-val2">test-label2</a></li>
            </ul>""")


class RangeWidgetTests(TestCase):

    def test_widget(self):
        w = RangeWidget()
        self.assertEqual(len(w.widgets), 2)
        self.assertHTMLEqual(w.render('price', ''), """
            <input type="text" name="price_0" />
            -
            <input type="text" name="price_1" />""")

        self.assertHTMLEqual(w.render('price', slice(5.99, 9.99)), """
            <input type="text" name="price_0" value="5.99" />
            -
            <input type="text" name="price_1" value="9.99" />""")

