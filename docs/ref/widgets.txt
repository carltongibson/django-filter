Widget Reference
================

This is a reference document with a list of the provided widgets and their
arguments.

``LinkWidget``
~~~~~~~~~~~~~~

This widget renders each option as a link, instead of an actual <input>.  It has
one method that you can overide for additional customizability.
``option_string()`` should return a string with 3 Python keyword argument
placeholders::

1. ``attrs``: This is a string with all the attributes that will be on the
   final ``<a>`` tag.
2. ``query_string``: This is the query string for use in the ``href``
   option on the ``<a>`` elemeent.
3. ``label``: This is the text to be displayed to the user.
