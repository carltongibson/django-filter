DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'django_filters',
    'django_filters.tests'
)

ROOT_URLCONF = None

USE_TZ = True
