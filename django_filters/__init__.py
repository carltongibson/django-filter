# flake8: noqa
from __future__ import absolute_import

import pkgutil

from .constants import STRICTNESS
from .filterset import FilterSet
from .filters import *

# We make the `rest_framework` module available without an additional import.
#   If DRF is not installed, no-op.
if pkgutil.find_loader('rest_framework') is not None:
    from . import rest_framework
del pkgutil

__version__ = '1.1.0'


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
