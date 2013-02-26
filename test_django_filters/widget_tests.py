from __future__ import absolute_import
from __future__ import unicode_literals

from django.test import TestCase
from django.forms import TextInput, Select

from django_filters.widgets import RangeWidget
from django_filters.widgets import LinkWidget
from django_filters.widgets import LookupTypeWidget


class LookupTypeWidgetTests(TestCase):
    
    def test_widget_requires_field(self):
        with self.assertRaises(TypeError):
            LookupTypeWidget()

    def test_widget_render(self):
        widgets = [TextInput(), Select(choices=(('a', 'a'), ('b', 'b')))]
        w = LookupTypeWidget(widgets)
        self.assertHTMLEqual(w.render('price', ''), """
            <input name="price_0" type="text" />
            <select name="price_1">
                <option value="a">a</option>
                <option value="b">b</option>
            </select>""")

        self.assertHTMLEqual(w.render('price', None), """
            <input name="price_0" type="text" />
            <select name="price_1">
                <option value="a">a</option>
                <option value="b">b</option>
            </select>""")

        self.assertHTMLEqual(w.render('price', ['2', 'a']), """
            <input name="price_0" type="text" value="2" />
            <select name="price_1">
                <option selected="selected" value="a">a</option>
                <option value="b">b</option>
            </select>""")


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

        self.assertHTMLEqual(w.render('price', None), """
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

    def test_widget_with_option_groups(self):
        choices = (
            ('Audio', (
                    ('vinyl', 'Vinyl'),
                    ('cd', 'CD'),
                )
            ),
            ('Video', (
                    ('vhs', 'VHS Tape'),
                    ('dvd', 'DVD'),
                )
            ),
            ('unknown', 'Unknown'),
        )

        w = LinkWidget(choices=choices)
        self.assertHTMLEqual(w.render('media', ''), """
            <ul>
                <li><a href="?media=vinyl">Vinyl</a></li>
                <li><a href="?media=cd">CD</a></li>
                <li><a href="?media=vhs">VHS Tape</a></li>
                <li><a href="?media=dvd">DVD</a></li>
                <li><a href="?media=unknown">Unknown</a></li>
            </ul>""")

    def test_widget_with_blank_choice(self):
        choices = (
            ('', '---------'),
            ('test-val1', 'test-label1'),
            ('test-val2', 'test-label2'),
        )

        w = LinkWidget(choices=choices)
        self.assertHTMLEqual(w.render('price', ''), """
            <ul>
                <li><a class="selected" href="?price=">All</a></li>
                <li><a href="?price=test-val1">test-label1</a></li>
                <li><a href="?price=test-val2">test-label2</a></li>
            </ul>""")

    def test_widget_value_from_datadict(self):
        w = LinkWidget()
        data = {'price': 'test-val1'}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, 'test-val1')


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

