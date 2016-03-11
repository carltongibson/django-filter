import os
import sys
from setuptools import setup, find_packages

f = open('README.rst')
readme = f.read()
f.close()

version = '0.13.0'

if sys.argv[-1] == 'publish':
    if os.system("pip freeze | grep wheel"):
        print("wheel not installed.\nUse `pip install wheel`.\nExiting.")
        sys.exit()
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()

setup(
    name='django-filter',
    version=version,
    description=('Django-filter is a reusable Django application for allowing'
                 ' users to filter querysets dynamically.'),
    long_description=readme,
    author='Alex Gaynor',
    author_email='alex.gaynor@gmail.com',
    maintainer='Carlton Gibson',
    maintainer_email='carlton.gibson@noumenal.es',
    url='http://github.com/carltongibson/django-filter/tree/master',
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
)
