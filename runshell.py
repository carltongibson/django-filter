#!/usr/bin/env python
import os
import sys
from django.core.management import execute_from_command_line


def runshell():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    execute_from_command_line(sys.argv[:1] + ['migrate', '--noinput', '-v', '0'])
    execute_from_command_line(sys.argv[:1] + ['shell'] + sys.argv[1:])

if __name__ == '__main__':
    runshell()
