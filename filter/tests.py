__test__ = {"filterset": """
>>> from django import forms
>>> from django.core.management import call_command
>>> import filter
>>> from filter import FilterSet
>>> from filter.models import User, STATUS_CHOICES

>>> call_command('loaddata', 'test_users', verbosity=0)

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

>>> class F(FilterSet):
...     class Meta:
...         model = User
...         fields = ['status']

>>> f = F({'status': '1'}, queryset=User.objects.all())
>>> f.qs
[<User: alex>]
>>> print f.form
<tr><th><label for="id_status">Status:</label></th><td><select name="status" id="id_status">
<option value="0">Regular</option>
<option value="1" selected="selected">Admin</option>
</select></td></tr>

>>> class F(FilterSet):
...     status = filter.ChoiceFilter(widget=forms.RadioSelect, choices=STATUS_CHOICES)
...     class Meta:
...         model = User
...         fields = ['status']

>>> f = F(queryset=User.objects.all())
>>> print f.form
<tr><th><label for="id_status_0">Status:</label></th><td><ul>
<li><label for="id_status_0"><input type="radio" id="id_status_0" value="0" name="status" /> Regular</label></li>
<li><label for="id_status_1"><input type="radio" id="id_status_1" value="1" name="status" /> Admin</label></li>
</ul></td></tr>

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

>>> class F(FilterSet):
...     status = filter.MultipleChoiceFilter(choices=STATUS_CHOICES)
...     class Meta:
...         model = User
...         fields = ['status']

>>> f = F(queryset=User.objects.all())
>>> print f.form
<tr><th><label for="id_status">Status:</label></th><td><select multiple="multiple" name="status" id="id_status">
<option value="0">Regular</option>
<option value="1">Admin</option>
</select></td></tr>
>>> f.qs
[<User: alex>, <User: aaron>, <User: jacob>]
>>> f = F({'status': ['0']}, queryset=User.objects.all())
>>> f.qs
[<User: aaron>, <User: jacob>]
>>> f = F({'status': ['0', '1']}, queryset=User.objects.all())
>>> f.qs
[<User: alex>, <User: aaron>, <User: jacob>]

"""}

