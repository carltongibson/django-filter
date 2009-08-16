import os

DEBUG = TEMPLATE_DEBUG = True
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = '/tmp/shorturls.db'
INSTALLED_APPS = (
    'django_filters',
    'django_filters.tests',
)
ROOT_URLCONF = 'django_filters.tests.test_urls'
TEMPLATE_DIRS = os.path.join(os.path.dirname(__file__), 'tests', 'templates')
