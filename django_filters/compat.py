
from __future__ import absolute_import

import django
from django.conf import settings
from django.utils.timezone import make_aware as make_aware_orig

try:
    from django.forms.utils import pretty_name
except ImportError:  # Django 1.8
    from django.forms.forms import pretty_name

# django-crispy-forms is optional
try:
    import crispy_forms
except ImportError:
    crispy_forms = None


def is_crispy():
    return 'crispy_forms' in settings.INSTALLED_APPS and crispy_forms


# coreapi is optional (Note that uritemplate is a dependency of coreapi)
# Fixes #525 - cannot simply import from rest_framework.compat, due to
# import issues w/ django-guardian.
try:
    import coreapi
except ImportError:
    coreapi = None

try:
    import coreschema
except ImportError:
    coreschema = None

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



def make_aware(value, timezone, is_dst):
    """is_dst was added for 1.9"""
    if django.VERSION >= (1, 9):
        return make_aware_orig(value, timezone, is_dst)
    else:
        return make_aware_orig(value, timezone)
