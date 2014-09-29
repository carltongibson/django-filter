from setuptools import setup, find_packages

f = open('README.rst')
readme = f.read()
f.close()

setup(
    name='django-filter',
    version='0.7',
    description=('Django-filter is a reusable Django application for allowing'
                 ' users to filter querysets dynamically.'),
    long_description=readme,
    author='Alex Gaynor',
    author_email='alex.gaynor@gmail.com',
    url='http://github.com/alex/django-filter/tree/master',
    packages=find_packages(exclude=['tests']),
    package_data = {
        'django_filters': [
            'locale/*/LC_MESSAGES/*',
        ],
    },
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
)
