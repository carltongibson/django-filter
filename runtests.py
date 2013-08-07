#!/usr/bin/env python
import sys
from django import VERSION
from django.conf import settings
from django.core.management import execute_from_command_line

if not settings.configured:
    test_runners_args = {}
    if VERSION[1] < 6:
        test_runners_args = {
            'TEST_RUNNER': 'discover_runner.DiscoverRunner',
        }
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            },
        },
        INSTALLED_APPS=(
            'django_filters',
            'tests',
        ),
        ROOT_URLCONF=None,
        USE_TZ=True,
        SECRET_KEY='foobar',
        **test_runners_args
    )


def runtests():
    argv = sys.argv[:1] + ['test'] + sys.argv[1:]
    execute_from_command_line(argv)


if __name__ == '__main__':
    runtests()
