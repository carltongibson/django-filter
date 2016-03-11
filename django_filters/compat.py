
import django


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
