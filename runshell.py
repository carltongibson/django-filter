#!/usr/bin/env python
import os
import sys
from django.core.management import execute_from_command_line


def runshell():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    execute_from_command_line(sys.argv[:1] + ['migrate', '--noinput', '-v', '0'])
    argv = sys.argv[:1] + ['shell'] + sys.argv[1:]
    execute_from_command_line(argv)

if __name__ == '__main__':
    runshell()
