
from django.conf import settings as dj_settings
from django.core.signals import setting_changed
from django.utils.translation import ugettext_lazy as _

from .utils import deprecate


DEFAULTS = {
    'HELP_TEXT_FILTER': True,
    'HELP_TEXT_EXCLUDE': True,
    'VERBOSE_LOOKUPS': {
        # transforms don't need to be verbose, since their expressions are chained
        'date': _('date'),
        'year': _('year'),
        'month': _('month'),
        'day': _('day'),
        'week_day': _('week day'),
        'hour': _('hour'),
        'minute': _('minute'),
        'second': _('second'),

        # standard lookups
        'exact': _(''),
        'iexact': _(''),
        'contains': _('contains'),
        'icontains': _('contains'),
        'in': _('is in'),
        'gt': _('is greater than'),
        'gte': _('is greater than or equal to'),
        'lt': _('is less than'),
        'lte': _('is less than or equal to'),
        'startswith': _('starts with'),
        'istartswith': _('starts with'),
        'endswith': _('ends with'),
        'iendswith': _('ends with'),
        'range': _('is in range'),
        'isnull': _(''),
        'regex': _('matches regex'),
        'iregex': _('matches regex'),
        'search': _('search'),

        # postgres lookups
        'contained_by': _('is contained by'),
        'overlap': _('overlaps'),
        'has_key': _('has key'),
        'has_keys': _('has keys'),
        'has_any_keys': _('has any keys'),
        'trigram_similar': _('search'),
    },
}


DEPRECATED_SETTINGS = [
    'HELP_TEXT_FILTER',
    'HELP_TEXT_EXCLUDE'
]


class Settings(object):

    def __init__(self):
        for setting in DEFAULTS:
            value = self.get_setting(setting)
            setattr(self, setting, value)

    def VERBOSE_LOOKUPS():
        """
        VERBOSE_LOOKUPS accepts a dictionary of {terms: verbose expressions}
        or a zero-argument callable that returns a dictionary.
        """
        def fget(self):
            if callable(self._VERBOSE_LOOKUPS):
                self._VERBOSE_LOOKUPS = self._VERBOSE_LOOKUPS()
            return self._VERBOSE_LOOKUPS

        def fset(self, value):
            self._VERBOSE_LOOKUPS = value

        return locals()
    VERBOSE_LOOKUPS = property(**VERBOSE_LOOKUPS())

    def get_setting(self, setting):
        django_setting = 'FILTERS_%s' % setting

        if setting in DEPRECATED_SETTINGS and hasattr(dj_settings, django_setting):
            deprecate("The '%s' setting has been deprecated." % django_setting)

        return getattr(dj_settings, django_setting, DEFAULTS[setting])

    def change_setting(self, setting, value, enter, **kwargs):
        if not setting.startswith('FILTERS_'):
            return
        setting = setting[8:]  # strip 'FILTERS_'

        # ensure a valid app setting is being overridden
        if setting not in DEFAULTS:
            return

        # if exiting, refetch the value from settings.
        value = value if enter else self.get_setting(setting)
        setattr(self, setting, value)


settings = Settings()
setting_changed.connect(settings.change_setting)
