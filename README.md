# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/carltongibson/django-filter/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                            |    Stmts |     Miss |   Cover |   Missing |
|------------------------------------------------ | -------: | -------: | ------: | --------: |
| django\_filters/\_\_init\_\_.py                 |       19 |        1 |     95% |        27 |
| django\_filters/compat.py                       |       15 |        2 |     87% |       6-7 |
| django\_filters/conf.py                         |       34 |        0 |    100% |           |
| django\_filters/constants.py                    |        2 |        0 |    100% |           |
| django\_filters/exceptions.py                   |        4 |        0 |    100% |           |
| django\_filters/fields.py                       |      182 |        0 |    100% |           |
| django\_filters/filters.py                      |      368 |        1 |     99% |       494 |
| django\_filters/filterset.py                    |      216 |        0 |    100% |           |
| django\_filters/rest\_framework/\_\_init\_\_.py |        3 |        0 |    100% |           |
| django\_filters/rest\_framework/backends.py     |       85 |       15 |     82% |86-90, 96-118 |
| django\_filters/rest\_framework/filters.py      |        8 |        0 |    100% |           |
| django\_filters/rest\_framework/filterset.py    |       22 |        0 |    100% |           |
| django\_filters/utils.py                        |      147 |        1 |     99% |       242 |
| django\_filters/views.py                        |       55 |        0 |    100% |           |
| django\_filters/widgets.py                      |      160 |        0 |    100% |           |
|                                       **TOTAL** | **1320** |   **20** | **98%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/carltongibson/django-filter/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/carltongibson/django-filter/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/carltongibson/django-filter/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/carltongibson/django-filter/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fcarltongibson%2Fdjango-filter%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/carltongibson/django-filter/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.