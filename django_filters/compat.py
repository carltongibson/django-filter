
from __future__ import absolute_import

import django
from django.conf import settings


# django-crispy-forms is optional
try:
    import crispy_forms
except ImportError:
    crispy_forms = None

is_crispy = 'crispy_forms' in settings.INSTALLED_APPS and crispy_forms


# coreapi only compatible with DRF 3.4+
try:
    from rest_framework.compat import coreapi
except ImportError:
    coreapi = None


def remote_field(field):
    """
    https://docs.djangoproject.com/en/1.9/releases/1.9/#field-rel-changes
    """
    if django.VERSION >= (1, 9):
        return field.remote_field
    return field.rel


def remote_model(field):
    if django.VERSION >= (1, 9):
        return remote_field(field).model
    return remote_field(field).to


def remote_queryset(field):
    model = remote_model(field)
    limit_choices_to = field.get_limit_choices_to()

    return model._default_manager.complex_filter(limit_choices_to)


def format_value(widget, value):
    if django.VERSION >= (1, 10):
        return widget.format_value(value)
    return widget._format_value(value)
