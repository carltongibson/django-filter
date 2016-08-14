# flake8: noqa
from __future__ import absolute_import
from .filterset import FilterSet
from .filters import *

__version__ = '0.14.0'


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
