
from django.test import TestCase, override_settings

from django_filters.conf import is_callable, settings


class DefaultSettingsTests(TestCase):

    def test_verbose_lookups(self):
        self.assertIsInstance(settings.VERBOSE_LOOKUPS, dict)
        self.assertIn('exact', settings.VERBOSE_LOOKUPS)

    def test_disable_help_text(self):
        self.assertFalse(settings.DISABLE_HELP_TEXT)

    def test_empty_choice_label(self):
        self.assertEqual(settings.EMPTY_CHOICE_LABEL, '---------')

    def test_null_choice_label(self):
        self.assertIsNone(settings.NULL_CHOICE_LABEL)

    def test_null_choice_value(self):
        self.assertEqual(settings.NULL_CHOICE_VALUE, 'null')


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
        self.assertFalse(hasattr(dj_settings, 'FILTERS_DISABLE_HELP_TEXT'))

        # Default value
        self.assertFalse(settings.DISABLE_HELP_TEXT)

        with override_settings(FILTERS_DISABLE_HELP_TEXT=True):
            self.assertTrue(settings.DISABLE_HELP_TEXT)

        # Revert to default
        self.assertFalse(settings.DISABLE_HELP_TEXT)

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
