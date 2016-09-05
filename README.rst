Django Filter
=============

Django-filter is a reusable Django application for allowing users to filter
querysets dynamically.

Full documentation on `read the docs`_.

.. image:: https://travis-ci.org/carltongibson/django-filter.svg?branch=master
    :target: https://travis-ci.org/carltongibson/django-filter

Requirements
------------

* Python 2.7, 3.3, 3.4, 3.5
* Django 1.8, 1.9, 1.10
* DRF 3.3 (Django 1.8 only), 3.4

Installation
------------

Install using pip::

    pip install django-filter

Or clone the repo and add to your PYTHONPATH::

    git clone git@github.com:carltongibson/django-filter.git

Usage
-----

Django-filter can be used for generating interfaces similar to the Django
admin's ``list_filter`` interface.  It has an API very similar to Django's
``ModelForms``.  For example, if you had a Product model you could have a
filterset for it with the code::

    import django_filters

    class ProductFilter(django_filters.FilterSet):
        class Meta:
            model = Product
            fields = ['name', 'price', 'manufacturer']


And then in your view you could do::

    def product_list(request):
        filter = ProductFilter(request.GET, queryset=Product.objects.all())
        return render(request, 'my_app/template.html', {'filter': filter})

Django-filters additionally supports specifying FilterSet fields using a
dictionary to specify filters with lookup types::

    import django_filters

    class ProductFilter(django_filters.FilterSet):
        class Meta:
            model = Product
            fields = {'name': ['exact', 'icontains'],
                      'price': ['exact', 'gte', 'lte'],
                     }

The filters will be available as 'name', 'name__icontains', 'price',
'price__gte', and 'price__lte' in the above example.

Support
-------

If you have questions about usage or development you can join the
`mailing list`_.

.. _`read the docs`: https://django-filter.readthedocs.io/en/latest/
.. _`mailing list`: http://groups.google.com/group/django-filter
