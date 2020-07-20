from django.db import models
from unittest import mock


class MockQuerySet:
    """
    Generate a mock that is suitably similar to a QuerySet
    """

    def __new__(self):
        m = mock.Mock(spec_set=models.QuerySet())
        m.filter.return_value = m
        m.all.return_value = m
        return m
