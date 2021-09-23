Django Filter
=============

Django-filter is a reusable Django application allowing users to declaratively
add dynamic ``QuerySet`` filtering from URL parameters.

Full documentation on `read the docs`_.

.. image:: https://codecov.io/gh/carltongibson/django-filter/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/carltongibson/django-filter

.. image:: https://badge.fury.io/py/django-filter.svg
    :target: http://badge.fury.io/py/django-filter


Versioning and stability policy
-------------------------------

Django-Filter is a mature and stable package. It uses a two-part CalVer
versioning scheme, such as ``21.1``. The first number is the year. The second
is the release number within that year.

On an on-going basis, Django-Filter aims to support all current Django
versions, the matching current Python versions, and the latest version of
Django REST Framework.

Please see:

* `Status of supported Python branches <https://devguide.python.org/#status-of-python-branches>`_
* `List of supported Django versions <https://www.djangoproject.com/download/#support-versions>`_

Support for Python and Django versions will be dropped when they reach
end-of-life. Support for Python versions will dropped when they reach
end-of-life, even when still supported by a current version of Django.

Other breaking changes are rare. Where required, every effort will be made to
apply a "Year plus two" deprecation period. For example, a change initially
introduced in ``23.x`` would offer a fallback where feasible and finally be
removed in ``25.1``. Where fallbacks are not feasible, breaking changes without
deprecation will be called out in the release notes.


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

If you need help you can start a `discussion`_. For commercial support, please
`contact Carlton Gibson via his website <https://noumenal.es/>`_.

.. _`discussion`: https://github.com/carltongibson/django-filter/discussions
.. _`read the docs`: https://django-filter.readthedocs.io/en/main/
.. _`DRF integration docs`: https://django-filter.readthedocs.io/en/stable/guide/rest_framework.html
