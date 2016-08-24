
from __future__ import absolute_import
from copy import deepcopy

from django.db import models

from django_filters import filterset
from ..filters import BooleanFilter, IsoDateTimeFilter
from ..widgets import BooleanWidget


FILTER_FOR_DBFIELD_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
FILTER_FOR_DBFIELD_DEFAULTS.update({
    models.DateTimeField: {'filter_class': IsoDateTimeFilter},
    models.BooleanField: {
        'filter_class': BooleanFilter,
        'extra': lambda f: {
            'widget': BooleanWidget,
        },
    },
})


class FilterSet(filterset.FilterSet):
    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS
