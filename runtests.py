#!/usr/bin/env python
import sys
from django.conf import settings
from django.core.management import call_command

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
            'django_filters.tests',
        ),
        ROOT_URLCONF=None,
        USE_TZ=True,
        SECRET_KEY='foobar'
    )


def runtests():
    call_command('test', *sys.argv[1:], verbosity=2)

if __name__ == '__main__':
    runtests()
