Django Filter
=============

Django-filter is a reusable Django application allowing users to declaratively
add dynamic ``QuerySet`` filtering from URL parameters.

Full documentation on `read the docs`_.

.. image:: https://codecov.io/gh/carltongibson/django-filter/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/carltongibson/django-filter

.. image:: https://badge.fury.io/py/django-filter.svg
    :target: http://badge.fury.io/py/django-filter

Requirements
------------

* **Python**: 3.5, 3.6, 3.7, 3.8, 3.9
* **Django**: 2.2, 3.0, 3.1
* **DRF**: 3.10+

From Version 2.0 Django Filter is Python 3 only.
If you need to support Python 2.7 use the version 1.1 release.


Installation
------------

Install using pip:

.. code-block:: sh

    pip install django-filter

Then add ``'django_filters'`` to your ``INSTALLED_APPS``.

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'django_filters',
    ]


Usage
-----

Django-filter can be used for generating interfaces similar to the Django
admin's ``list_filter`` interface.  It has an API very similar to Django's
``ModelForms``.  For example, if you had a Product model you could have a
filterset for it with the code:

.. code-block:: python

    import django_filters

    class ProductFilter(django_filters.FilterSet):
        class Meta:
            model = Product
            fields = ['name', 'price', 'manufacturer']


And then in your view you could do:

.. code-block:: python

    def product_list(request):
        filter = ProductFilter(request.GET, queryset=Product.objects.all())
        return render(request, 'my_app/template.html', {'filter': filter})


Usage with Django REST Framework
--------------------------------

Django-filter provides a custom ``FilterSet`` and filter backend for use with
Django REST Framework.

To use this adjust your import to use
``django_filters.rest_framework.FilterSet``.

.. code-block:: python

    from django_filters import rest_framework as filters

    class ProductFilter(filters.FilterSet):
        class Meta:
            model = Product
            fields = ('category', 'in_stock')


For more details see the `DRF integration docs`_.


Support
-------

If you have questions about usage or development you can join the
`mailing list`_.

.. _`read the docs`: https://django-filter.readthedocs.io/en/master/
.. _`mailing list`: http://groups.google.com/group/django-filter
.. _`DRF integration docs`: https://django-filter.readthedocs.io/en/master/guide/rest_framework.html
