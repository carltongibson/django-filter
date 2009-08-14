from setuptools import setup, find_packages

f = open('README.txt')
readme = f.read()
f.close()

setup(
    name='django-filter',
    version='0.5.0',
    description='Django-filter is a reusable Django application for allowing users to filter queryset dynamically.',
    long_description=readme,
    author='Alex Gaynor',
    author_email='alex.gaynor@gmail.com',
    url='http://github.com/alex/django-filter/tree/master',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    package_data = {
        'django_filters': [
            'fixtures/*.json',
        ],
        'django_filters.tests': [
            'templates/django_filters/*.html',
        ]
    },
    zip_safe=False,
)
