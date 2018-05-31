from django.conf import settings

try:
    from django.db.models.sql.constants import QUERY_TERMS
except ImportError:
    # Django 2.1+ does not have QUERY_TERMS anymore
    QUERY_TERMS = {
        'contains', 'day', 'endswith', 'exact', 'gt', 'gte', 'hour',
        'icontains', 'iendswith', 'iexact', 'in', 'iregex', 'isnull',
        'istartswith', 'lt', 'lte', 'minute', 'month', 'range', 'regex',
        'search', 'second', 'startswith', 'week_day', 'year',
    }

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
