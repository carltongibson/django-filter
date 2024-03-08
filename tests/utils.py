from unittest import mock

import django
from django.db import models
from django.test import TestCase

if django.VERSION < (4, 2):
    class TestCase(TestCase):
        assertQuerySetEqual = TestCase.assertQuerysetEqual


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
