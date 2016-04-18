#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line


def runshell():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    execute_from_command_line(
        sys.argv[:1] +
        ['migrate', '--noinput', '-v', '0'] +
        (['--run-syncdb'] if django.VERSION >= (1, 9) else []))

    argv = sys.argv[:1] + ['shell'] + sys.argv[1:]
    execute_from_command_line(argv)

if __name__ == '__main__':
    runshell()
