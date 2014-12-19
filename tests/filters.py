#!/usr/bin/env python
# coding: utf-8
from django_filters import filterset
from .models import Book


class BookFilterSet(filterset.FilterSet):
    class Meta:
        model = Book
        fields = ['title', 'price', 'average_rating']
        order_by = ['title', 'price', 'average_rating', '-title', '-price', '-average_rating']