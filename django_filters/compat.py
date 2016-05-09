
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


def remote_queryset(field):
    model = remote_model(field)
    limit_choices_to = field.get_limit_choices_to()

    return model._default_manager.complex_filter(limit_choices_to)
