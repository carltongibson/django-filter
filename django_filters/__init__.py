# flake8: noqa
from __future__ import absolute_import
from .constants import STRICTNESS
from .filterset import FilterSet
from .filters import *

# We make the `rest_framework` module available without an additional import.
#   If DRF is not installed we simply set None.
try:
    from . import rest_framework
except ImportError:
    rest_framework = None

__version__ = '1.0.4'


def parse_version(version):
    '''
    '0.1.2-dev' -> (0, 1, 2, 'dev')
    '0.1.2' -> (0, 1, 2)
    '''
    v = version.split('.')
    v = v[:-1] + v[-1].split('-')
    ret = []
    for p in v:
        if p.isdigit():
            ret.append(int(p))
        else:
            ret.append(p)
    return tuple(ret)

VERSION = parse_version(__version__)
