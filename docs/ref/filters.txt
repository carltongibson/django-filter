Filter Reference
================

This is a reference document with a list of the filters and their arguments.

Filters
-------

``CharFilter``
~~~~~~~~~~~~~~

This filter does simple character matches, used with ``CharField`` and
``TextField`` by default.

``BooleanFilter``
~~~~~~~~~~~~~~~~~

This filter matches a boolean, either ``True`` or ``False``, used with
``BooleanField`` and ``NullBooleanField`` by default.

``ChoiceFilter``
~~~~~~~~~~~~~~~~

This filter matches an item of any type by choices, used with any field that
has ``choices``.

``MultipleChoiceFilter``
~~~~~~~~~~~~~~~~~~~~~~~~

The same as ``ChoiceFilter`` except the user can select multiple items and it
selects the OR of all the choices.

``DateFilter``
~~~~~~~~~~~~~~

Matches on a date.  Used with ``DateField`` by default.

``DateTimeFilter``
~~~~~~~~~~~~~~~~~~

Matches on a date and time.  Used with ``DateTimeField`` by default.

``TimeFilter``
~~~~~~~~~~~~~~

Matches on a time.  Used with ``TimeField`` by default.

``ModelChoiceFilter``
~~~~~~~~~~~~~~~~~~~~~

Similar to a ``ChoiceFilter`` except it works with related models, used for
``ForeignKey`` by default.

``ModelMultipleChoiceFilter``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similar to a ``MultipleChoiceFilter`` except it works with related models, used
for ``ManyToManyField`` by default.

``NumberFilter``
~~~~~~~~~~~~~~~~

Filters based on a numerical value, used with ``IntegerField``, ``FloatField``,
and ``DecimalField`` by default.

``RangeFilter``
~~~~~~~~~~~~~~~

Filters where a value is between two numerical values.

``DateRangeFilter``
~~~~~~~~~~~~~~~~~~~

Filter similar to the admin changelist date one, it has a number of common
selections for working with date fields.

``AllValuesFilter``
~~~~~~~~~~~~~~~~~~~

This is a ``ChoiceFilter`` whose choices are the current values in the
database.  So if in the DB for the given field you have values of 5, 7, and 9
each of those is present as an option.  This is similar to the default behavior
of the admin.

Core Arguments
--------------

``name``
~~~~~~~~

The name of the field this filter is supposed to filter on, if this is not
provided it automatically becomes the filter's name on the ``FilterSet``.

``label``
~~~~~~~~~

The label as it will apear in the HTML, analogous to a form field's label
argument.

``widget``
~~~~~~~~~~

The django.form Widget class which will represent the ``Filter``.  In addition
to the widgets that are included with Django that you can use there are
additional ones that django-filter provides which may be useful:

    * ``django_filters.widgets.LinkWidget`` -- this displays the options in a
      mannner similar to the way the Django Admin does, as a series of links.
      The link for the selected option will have ``class="selected"``.

``action``
~~~~~~~~~~

An optional callable that tells the filter how to handle the queryset.  It
recieves a ``QuerySet`` and the value to filter on and should return a
``Queryset`` that is filtered appropriately.

``lookup_type``
~~~~~~~~~~~~~~~

The type of lookup that should be performed using the Django ORM.  All the
normal options are allowed, and should be provided as a string.  You can also
provide either ``None`` or a ``list`` or a ``tuple``.  If ``None`` is provided,
then the user can select the lookup type from all the ones available in the Django
ORM.  If a ``list`` or ``tuple`` is provided, then the user can select from those
options.

``distinct``
~~~~~~~~~~~~

A boolean value that specifies whether the Filter will use distinct on the
queryset. This option can be used to eliminate duplicate results when using filters that span related models. Defaults to ``False``.

``exclude``
~~~~~~~~~~~

A boolean value that specifies whether the Filter should use ``filter`` or ``exclude`` on the queryset.
Defaults to ``False``.


``**kwargs``
~~~~~~~~~~~~

Any extra keyword arguments will be provided to the accompanying form Field.
This can be used to provide arguments like ``choices`` or ``queryset``.
