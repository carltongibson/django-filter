
from django.test import TestCase, override_settings

from django_filters.conf import settings


class DefaultSettingsTests(TestCase):

    def test_verbose_loookups(self):
        self.assertIsInstance(settings.VERBOSE_LOOKUPS, dict)
        self.assertIn('exact', settings.VERBOSE_LOOKUPS)

    def test_help_text_filter(self):
        self.assertTrue(settings.HELP_TEXT_FILTER)

    def test_help_text_exclude(self):
        self.assertTrue(settings.HELP_TEXT_EXCLUDE)


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
