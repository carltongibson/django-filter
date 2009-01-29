__test__ = {"filterset": """
>>> from filter import FilterSet
>>> from django.contrib.auth.models import User
>>> class F(FilterSet):
...     class Meta:
...         model = User

>>> F.base_filters.keys()
['username', 'first_name', 'last_name', 'password']

>>> class F(FilterSet):
...     class Meta:
...         model = User
...         exclude = ['password']

>>> F.base_filters.keys()
['username', 'first_name', 'last_name']

"""}

