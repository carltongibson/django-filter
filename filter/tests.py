__test__ = {"filterset": """
>>> import filter
>>> from filter import FilterSet
>>> from filter.models import User

>>> User.objects.all()
[]
>>> _ = User.objects.create(username='alex', status=1)
>>> _ = User.objects.create(username='aaron')
>>> _ = User.objects.create(username='jacob')
>>> User.objects.count()
3

>>> class F(FilterSet):
...     class Meta:
...         model = User

>>> F.base_filters.keys()
['username', 'first_name', 'last_name', 'status', 'is_active']


>>> class F(FilterSet):
...     class Meta:
...         model = User
...         exclude = ['is_active']

>>> F.base_filters.keys()
['username', 'first_name', 'last_name', 'status']

>>> f = F({'status': '1'}, queryset=User.objects.all())
>>> f.qs
[<User: alex>]

>>> class F(FilterSet):
...     class Meta:
...         model = User
...         fields = ['username']

>>> F.base_filters.keys()
['username']

>>> f = F(queryset=User.objects.all())
>>> f.qs
[<User: alex>, <User: aaron>, <User: jacob>]
>>> f = F({'username': 'alex'}, queryset=User.objects.all())
>>> f.qs
[<User: alex>]
>>> print f.form
<tr><th><label for="id_username">Username:</label></th><td><input type="text" name="username" value="alex" id="id_username" /></td></tr>

>>> class F(FilterSet):
...     username = filter.CharFilter(action=lambda qs, value: qs.filter(**{'username__startswith': value}))
...     class Meta:
...         model = User
...         fields = ['username']

>>> f = F({'username': 'a'}, queryset=User.objects.all())
>>> f.qs
[<User: alex>, <User: aaron>]

"""}

