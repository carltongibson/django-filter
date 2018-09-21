from unittest import mock

from django.db import models


class MockQuerySet:
    """
    Generate a mock that is suitably similar to a QuerySet
    """

    def __new__(self):
        m = mock.Mock(spec_set=models.QuerySet())
        m._next_is_sticky.return_value = m
        m.filter.return_value = m
        m.all.return_value = m
        return m
