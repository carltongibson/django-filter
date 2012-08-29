Django-filter is a reusable Django application for allowing users to filter
querysets dynamically.  It requires Python 2.4 or higher.  For usage and
installation instructions consult the docs directory.

Django-filter can be used for generating interfaces similar to the Django
admin's ``list_filter`` interface.  It has an API very similar to Django's
``ModelForms``.  For example, if you had a Product model you could have a
filterset for it with the code::

    import django_filters

    class ProductFilterSet(django_filters.FilterSet):
        class Meta:
            model = Product
            fields = ['name', 'price', 'manufacturer']


And then in your view you could do::

    def product_list(request):
        filterset = ProductFilterSet(request.GET or None)
        return render_to_response('product/product_list.html',
            {'filterset': filterset})


See the docs directory for more information.

If you have questions about usage or development you can join the
mailing list at: http://groups.google.com/group/django-filter
