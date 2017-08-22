
from django.test import TestCase, override_settings

from django_filters import STRICTNESS, FilterSet
from django_filters.conf import is_callable, settings
from tests.models import User


class DefaultSettingsTests(TestCase):

    def test_verbose_lookups(self):
        self.assertIsInstance(settings.VERBOSE_LOOKUPS, dict)
        self.assertIn('exact', settings.VERBOSE_LOOKUPS)

    def test_disable_help_text(self):
        self.assertFalse(settings.DISABLE_HELP_TEXT)

    def test_strictness(self):
        self.assertEqual(settings.STRICTNESS, STRICTNESS.RETURN_NO_RESULTS)

    def test_help_text_filter(self):
        self.assertTrue(settings.HELP_TEXT_FILTER)

    def test_help_text_exclude(self):
        self.assertTrue(settings.HELP_TEXT_EXCLUDE)

    def test_empty_choice_label(self):
        self.assertEqual(settings.EMPTY_CHOICE_LABEL, '---------')

    def test_null_choice_label(self):
        self.assertIsNone(settings.NULL_CHOICE_LABEL)

    def test_null_choice_value(self):
        self.assertEqual(settings.NULL_CHOICE_VALUE, 'null')


class StrictnessTests(TestCase):
    class F(FilterSet):
        class Meta:
            model = User
            fields = []

    def test_settings_default(self):
        self.assertEqual(self.F().strict, STRICTNESS.RETURN_NO_RESULTS)

    def test_ignore(self):
        with override_settings(FILTERS_STRICTNESS=STRICTNESS.IGNORE):
            self.assertEqual(self.F().strict, STRICTNESS.IGNORE)

    def test_return_no_results(self):
        with override_settings(FILTERS_STRICTNESS=STRICTNESS.RETURN_NO_RESULTS):
            self.assertEqual(self.F().strict, STRICTNESS.RETURN_NO_RESULTS)

    def test_raise_validation_error(self):
        with override_settings(FILTERS_STRICTNESS=STRICTNESS.RAISE_VALIDATION_ERROR):
            self.assertEqual(self.F().strict, STRICTNESS.RAISE_VALIDATION_ERROR)

    def test_legacy_ignore(self):
        with override_settings(FILTERS_STRICTNESS=False):
            self.assertEqual(self.F().strict, STRICTNESS.IGNORE)

    def test_legacy_return_no_results(self):
        with override_settings(FILTERS_STRICTNESS=True):
            self.assertEqual(self.F().strict, STRICTNESS.RETURN_NO_RESULTS)

    def test_legacy_raise_validation_error(self):
        with override_settings(FILTERS_STRICTNESS='RAISE'):
            self.assertEqual(self.F().strict, STRICTNESS.RAISE_VALIDATION_ERROR)

    def test_legacy_differentiation(self):
        self.assertNotEqual(STRICTNESS.IGNORE, False)
        self.assertNotEqual(STRICTNESS.RETURN_NO_RESULTS, True)
        self.assertNotEqual(STRICTNESS.RAISE_VALIDATION_ERROR, 'RAISE')


class OverrideSettingsTests(TestCase):

    def test_attribute_override(self):
        self.assertIsInstance(settings.VERBOSE_LOOKUPS, dict)

        original = settings.VERBOSE_LOOKUPS

        with override_settings(FILTERS_VERBOSE_LOOKUPS=None):
            self.assertIsNone(settings.VERBOSE_LOOKUPS)

        self.assertIs(settings.VERBOSE_LOOKUPS, original)

    def test_missing_attribute_override(self):
        # ensure that changed setting behaves correctly when
        # not originally present in the user's settings.
        from django.conf import settings as dj_settings
        self.assertFalse(hasattr(dj_settings, 'FILTERS_HELP_TEXT_FILTER'))

        # Default value
        self.assertTrue(settings.HELP_TEXT_FILTER)

        with override_settings(FILTERS_HELP_TEXT_FILTER=None):
            self.assertIsNone(settings.HELP_TEXT_FILTER)

        # Revert to default
        self.assertTrue(settings.HELP_TEXT_FILTER)

    def test_non_filters_setting(self):
        self.assertFalse(hasattr(settings, 'USE_TZ'))

        with override_settings(USE_TZ=False):
            self.assertFalse(hasattr(settings, 'USE_TZ'))

        self.assertFalse(hasattr(settings, 'USE_TZ'))

    def test_non_existent_setting(self):
        self.assertFalse(hasattr(settings, 'FILTERS_FOOBAR'))
        self.assertFalse(hasattr(settings, 'FOOBAR'))

        with override_settings(FILTERS_FOOBAR='blah'):
            self.assertFalse(hasattr(settings, 'FILTERS_FOOBAR'))
            self.assertFalse(hasattr(settings, 'FOOBAR'))

        self.assertFalse(hasattr(settings, 'FILTERS_FOOBAR'))
        self.assertFalse(hasattr(settings, 'FOOBAR'))


class IsCallableTests(TestCase):

    def test_behavior(self):
        def func():
            pass

        class Class(object):
            def __call__(self):
                pass

            def method(self):
                pass

        c = Class()

        self.assertTrue(is_callable(func))
        self.assertFalse(is_callable(Class))
        self.assertTrue(is_callable(c))
        self.assertTrue(is_callable(c.method))
