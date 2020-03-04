from django.forms import NumberInput, Select, TextInput
from django.test import TestCase

from django_filters.widgets import (
    BaseCSVWidget,
    BooleanWidget,
    CSVWidget,
    LinkWidget,
    LookupChoiceWidget,
    QueryArrayWidget,
    RangeWidget,
    SuffixedMultiWidget
)


class LookupTypeWidgetTests(TestCase):

    def test_widget_requires_field(self):
        with self.assertRaises(TypeError):
            LookupChoiceWidget()

    def test_widget_render(self):
        widgets = [TextInput(), Select(choices=(('a', 'a'), ('b', 'b')))]
        w = LookupChoiceWidget(widgets)
        self.assertHTMLEqual(w.render('price', ''), """
            <input name="price" type="text" />
            <select name="price_lookup">
                <option value="a">a</option>
                <option value="b">b</option>
            </select>""")

        self.assertHTMLEqual(w.render('price', None), """
            <input name="price" type="text" />
            <select name="price_lookup">
                <option value="a">a</option>
                <option value="b">b</option>
            </select>""")

        self.assertHTMLEqual(w.render('price', ['2', 'a']), """
            <input name="price" type="text" value="2" />
            <select name="price_lookup">
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
            )),
            ('Video', (
                ('vhs', 'VHS Tape'),
                ('dvd', 'DVD'),
            )),
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


class SuffixedMultiWidgetTests(TestCase):
    def test_assertions(self):
        # number of widgets must match suffixes
        with self.assertRaises(AssertionError):
            SuffixedMultiWidget(widgets=[BooleanWidget])

        # suffixes must be unique
        class W(SuffixedMultiWidget):
            suffixes = ['a', 'a']

        with self.assertRaises(AssertionError):
            W(widgets=[BooleanWidget, BooleanWidget])

        # should succeed
        class W(SuffixedMultiWidget):
            suffixes = ['a', 'b']
        W(widgets=[BooleanWidget, BooleanWidget])

    def test_render(self):
        class W(SuffixedMultiWidget):
            suffixes = ['min', 'max']

        w = W(widgets=[TextInput, TextInput])
        self.assertHTMLEqual(w.render('price', ''), """
            <input name="price_min" type="text" />
            <input name="price_max" type="text" />
        """)

        # blank suffix
        class W(SuffixedMultiWidget):
            suffixes = [None, 'lookup']

        w = W(widgets=[TextInput, TextInput])
        self.assertHTMLEqual(w.render('price', ''), """
            <input name="price" type="text" />
            <input name="price_lookup" type="text" />
        """)

    def test_value_from_datadict(self):
        class W(SuffixedMultiWidget):
            suffixes = ['min', 'max']

        w = W(widgets=[TextInput, TextInput])
        result = w.value_from_datadict({
            'price_min': '1',
            'price_max': '2',
        }, {}, 'price')
        self.assertEqual(result, ['1', '2'])

        result = w.value_from_datadict({}, {}, 'price')
        self.assertEqual(result, [None, None])

        # blank suffix
        class W(SuffixedMultiWidget):
            suffixes = ['', 'lookup']

        w = W(widgets=[TextInput, TextInput])
        result = w.value_from_datadict({
            'price': '1',
            'price_lookup': 'lt',
        }, {}, 'price')
        self.assertEqual(result, ['1', 'lt'])

    def test_value_omitted_from_data(self):
        class A(SuffixedMultiWidget):
            suffixes = ['b']

        a = A(widgets=[BooleanWidget])

        result = a.value_omitted_from_data([], None, 'test')

        self.assertIsNotNone(result)

    def test_replace_name(self):
        class A(SuffixedMultiWidget):
            suffixes = ['test']

        a = A(widgets=[None])

        output = '<div name="test123_0"></div>'
        index = 0
        q = a.replace_name(output, index)
        self.assertEqual(q, '<div name="test123_test"></div>')

    def test_decompress_value_none(self):
        class A(SuffixedMultiWidget):
            suffixes = ['']

        a = A(widgets=[None])
        self.assertEqual(a.decompress(None), [None, None])


class RangeWidgetTests(TestCase):

    def test_widget(self):
        w = RangeWidget()
        self.assertEqual(len(w.widgets), 2)
        self.assertHTMLEqual(w.render('price', ''), """
            <input type="text" name="price_min" />
            -
            <input type="text" name="price_max" />""")

        self.assertHTMLEqual(w.render('price', slice(5.99, 9.99)), """
            <input type="text" name="price_min" value="5.99" />
            -
            <input type="text" name="price_max" value="9.99" />""")

    def test_widget_attributes(self):
        w = RangeWidget(attrs={'type': 'date'})
        self.assertEqual(len(w.widgets), 2)
        self.assertHTMLEqual(w.render('date', ''), """
            <input type="date" name="date_min" />
            -
            <input type="date" name="date_max" />""")


class BooleanWidgetTests(TestCase):

    def test_widget_render(self):
        w = BooleanWidget()
        self.assertHTMLEqual(w.render('price', ''), """
            <select name="price">
                <option selected="selected" value="">Unknown</option>
                <option value="true">Yes</option>
                <option value="false">No</option>
            </select>""")

    def test_widget_value_from_datadict(self):
        """
        """
        w = BooleanWidget()

        trueActive = {'active': 'true'}
        result = w.value_from_datadict(trueActive, {}, 'active')
        self.assertEqual(result, True)

        falseActive = {'active': 'false'}
        result = w.value_from_datadict(falseActive, {}, 'active')
        self.assertEqual(result, False)

        result = w.value_from_datadict({}, {}, 'active')
        self.assertEqual(result, None)


class BaseCSVWidgetTests(TestCase):
    def test_widget_render(self):
        class NumberCSVWidget(BaseCSVWidget, NumberInput):
            pass

        w = NumberCSVWidget(attrs={'test': 'attr'})
        self.assertHTMLEqual(w.render('price', None), """
            <input type="number" test="attr" name="price" />""")

        self.assertHTMLEqual(w.render('price', ''), """
            <input type="number" test="attr" name="price" />""")

        self.assertHTMLEqual(w.render('price', []), """
            <input type="number" test="attr" name="price" />""")

        self.assertHTMLEqual(w.render('price', '1'), """
            <input type="number" test="attr" name="price" value="1" />""")

        self.assertHTMLEqual(w.render('price', '1,2'), """
            <input type="number" test="attr" name="price" value="1,2" />""")

        self.assertHTMLEqual(w.render('price', ['1', '2']), """
            <input type="text" name="price" value="1,2" />""")

        self.assertHTMLEqual(w.render('price', [1, 2]), """
            <input type="text" name="price" value="1,2" />""")

    def test_widget_value_from_datadict(self):
        class NumberCSVWidget(BaseCSVWidget, NumberInput):
            pass

        w = NumberCSVWidget()
        data = {'price': None}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, None)

        data = {'price': '1'}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, ['1'])

        data = {'price': '1,2'}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, ['1', '2'])

        data = {'price': '1,,2'}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, ['1', '', '2'])

        data = {'price': '1,'}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, ['1', ''])

        data = {'price': ','}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, ['', ''])

        data = {'price': ''}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, [])

        result = w.value_from_datadict({}, {}, 'price')
        self.assertEqual(result, None)

    def test_surrogate_class(self):
        class ClassSurrogate(BaseCSVWidget, NumberInput):
            surrogate = NumberInput

        w = ClassSurrogate()
        self.assertIsInstance(w.surrogate, NumberInput)

    def test_surrogate_instance(self):
        class InstanceSurrogate(BaseCSVWidget, NumberInput):
            surrogate = NumberInput()

        w = InstanceSurrogate()
        self.assertIsInstance(w.surrogate, NumberInput)
        self.assertIsNot(InstanceSurrogate.surrogate, w.surrogate)  # deepcopied


class CSVWidgetTests(TestCase):
    def test_widget_render(self):
        w = CSVWidget(attrs={'test': 'attr'})
        self.assertHTMLEqual(w.render('price', None), """
            <input type="text" test="attr" name="price" />""")

        self.assertHTMLEqual(w.render('price', ''), """
            <input type="text" test="attr" name="price" />""")

        self.assertHTMLEqual(w.render('price', []), """
            <input type="text" test="attr" name="price" />""")

        self.assertHTMLEqual(w.render('price', '1'), """
            <input type="text" test="attr" name="price" value="1" />""")

        self.assertHTMLEqual(w.render('price', '1,2'), """
            <input type="text" test="attr" name="price" value="1,2" />""")

        self.assertHTMLEqual(w.render('price', ['1', '2']), """
            <input type="text" test="attr" name="price" value="1,2" />""")

        self.assertHTMLEqual(w.render('price', [1, 2]), """
            <input type="text" test="attr" name="price" value="1,2" />""")


class CSVSelectTests(TestCase):
    class CSVSelect(BaseCSVWidget, Select):
        pass

    def test_widget(self):
        w = self.CSVSelect(choices=((1, 'a'), (2, 'b')))
        self.assertHTMLEqual(
            w.render('price', None),
            """
            <select name="price">
                <option value="1">a</option>
                <option value="2">b</option>
            </select>
            """
        )

        self.assertHTMLEqual(
            w.render('price', ''),
            """
            <select name="price">
                <option value="1">a</option>
                <option value="2">b</option>
            </select>
            """)

        self.assertHTMLEqual(
            w.render('price', '1'),
            """
            <select name="price">
                <option selected="selected" value="1">a</option>
                <option value="2">b</option>
            </select>
            """)

        self.assertHTMLEqual(
            w.render('price', '1,2'),
            """
            <select name="price">
                <option value="1">a</option>
                <option value="2">b</option>
            </select>
            """
        )

        self.assertHTMLEqual(w.render('price', ['1', '2']), """
            <input type="text" name="price" value="1,2" />""")

        self.assertHTMLEqual(w.render('price', [1, 2]), """
            <input type="text" name="price" value="1,2" />""")


class QueryArrayWidgetTests(TestCase):

    def test_widget_value_from_datadict(self):
        w = QueryArrayWidget()

        # Values can be provided as csv string: ?foo=bar,baz
        data = {'price': None}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, [])

        data = {'price': '1'}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, ['1'])

        data = {'price': '1,2'}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(sorted(result), ['1', '2'])

        data = {'price': '1,,2'}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(sorted(result), ['1', '2'])

        data = {'price': '1,'}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, ['1'])

        data = {'price': ','}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, [])

        data = {'price': ''}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, [])

        result = w.value_from_datadict({}, {}, 'price')
        self.assertEqual(result, [])

        # Values can be provided as query array: ?foo[]=bar&foo[]=baz

        data = {'price[]': None}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, [])

        data = {'price[]': ['1']}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, ['1'])

        data = {'price[]': ['1', '2']}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(sorted(result), ['1', '2'])

        data = {'price[]': ['1', '', '2']}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(sorted(result), ['1', '2'])

        data = {'price[]': ['1', '']}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, ['1'])

        data = {'price[]': ['', '']}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, [])

        data = {'price[]': []}
        result = w.value_from_datadict(data, {}, 'price')
        self.assertEqual(result, [])

        result = w.value_from_datadict({}, {}, 'price')
        self.assertEqual(result, [])
