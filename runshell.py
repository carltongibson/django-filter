#!/usr/bin/env python
import sys
from django.conf import settings
from django.core.management import call_command
from django.core.management import execute_from_command_line

if not settings.configured:
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
        SECRET_KEY='foobar'
    )


def runshell():
    call_command('syncdb', interactive=False)
    argv = sys.argv[:1] + ['shell'] + sys.argv[1:]
    execute_from_command_line(argv)

if __name__ == '__main__':
    runshell()
