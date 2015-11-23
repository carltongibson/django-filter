DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django_filters',
    'tests',
)

ROOT_URLCONF = 'tests.urls'

USE_TZ = True

SECRET_KEY = 'foobar'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
}]


SILENCED_SYSTEM_CHECKS = [
    '1_7.W001',  # Unset MIDDLEWARE_CLASSES warning
]
