
from django.test import TestCase

from django_filters.utils import get_model_field

from .models import User
from .models import HiredWorker
from .models import Business


class GetModelFieldTests(TestCase):

    def test_non_existent_field(self):
        result = get_model_field(User, 'unknown__name')
        self.assertIsNone(result)

    def test_related_field(self):
        result = get_model_field(Business, 'hiredworker__worker')
        self.assertEqual(result, HiredWorker._meta.get_field('worker'))
