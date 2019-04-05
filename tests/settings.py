
# ensure package/conf is importable
from django_filters.conf import DEFAULTS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.auth',
    'rest_framework',
    'django_filters',
    'tests.rest_framework',
    'tests',
)

MIDDLEWARE = []

ROOT_URLCONF = 'tests.urls'

USE_TZ = True

TIME_ZONE = 'UTC'

SECRET_KEY = 'foobar'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
}]


STATIC_URL = '/static/'


# XMLTestRunner output
TEST_OUTPUT_DIR = '.xmlcoverage'


# help verify that DEFAULTS is importable from conf.
def FILTERS_VERBOSE_LOOKUPS():
    return DEFAULTS['VERBOSE_LOOKUPS']
