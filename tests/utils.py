from unittest import mock

from django.db import models


class QuerySet(models.QuerySet):

    def __bool__(self):
        return True


class MockQuerySet:
    """
    Generate a mock that is suitably similar to a QuerySet
    """

    def __new__(self):
        m = mock.Mock(spec_set=QuerySet())
        m.filter.return_value = m
        m.all.return_value = m
        return m
