from rest_framework import fields

from ..filters import *


class BooleanFilter(BooleanFilter):
    field_class = fields.BooleanField


class NumberFilter(NumberFilter):
    field_class = fields.FloatField
