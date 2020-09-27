import os
import sys
from setuptools import setup, find_packages

# FIXME: Main module requires django to be present, so cannot run setup.py in
# clean environment.
# from django_filters import __version__
__version__ = '2.4.0'

f = open('README.rst')
readme = f.read()
f.close()

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
    print("  git tag -a %s -m 'version %s'" % (__version__, __version__))
    print("  git push --tags")
    sys.exit()

setup(
    name='django-filter',
    version=__version__,
    description=('Django-filter is a reusable Django application for allowing'
                 ' users to filter querysets dynamically.'),
    long_description=readme,
    author='Alex Gaynor',
    author_email='alex.gaynor@gmail.com',
    maintainer='Carlton Gibson',
    maintainer_email='carlton.gibson@noumenal.es',
    url='https://github.com/carltongibson/django-filter/tree/master',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Framework :: Django',
    ],
    zip_safe=False,
    python_requires='>=3.5',
    install_requires=[
        'Django>=2.2',
    ],
)
