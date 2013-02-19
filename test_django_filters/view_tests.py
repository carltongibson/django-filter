from __future__ import absolute_import
from __future__ import unicode_literals
from django.test import TestCase
from .models import Book


class GenericViewTestCase(TestCase):
    urls = 'test_django_filters.urls'
    
    def setUp(self):
        Book.objects.create(
            title="Ender's Game", price='1.00', average_rating=3.0)
        Book.objects.create(
            title="Rainbow Six", price='1.00', average_rating=3.0)
        Book.objects.create(
            title="Snowcrash", price='1.00', average_rating=3.0)


class GenericClassBasedViewTests(GenericViewTestCase):
    base_url = '/books/'

    def test_view(self):
        response = self.client.get(self.base_url)
        for b in ['Ender&#39;s Game', 'Rainbow Six', 'Snowcrash']:
            self.assertContains(response, b)

    def test_view_filtering_on_price(self):
        response = self.client.get(self.base_url + '?title=Snowcrash')
        for b in ['Ender&#39;s Game', 'Rainbow Six']:
            self.assertNotContains(response, b)
        self.assertContains(response, 'Snowcrash')


class GenericFunctionalViewTests(GenericViewTestCase):
    base_url = '/books-legacy/'

    def test_view(self):
        response = self.client.get(self.base_url)
        for b in ['Ender&#39;s Game', 'Rainbow Six', 'Snowcrash']:
            self.assertContains(response, b)

    def test_view_filtering_on_price(self):
        response = self.client.get(self.base_url + '?title=Snowcrash')
        for b in ['Ender&#39;s Game', 'Rainbow Six']:
            self.assertNotContains(response, b)
        self.assertContains(response, 'Snowcrash')

