# special field classes for testing

from django.db import models

class ChildOfCharField(models.CharField):
    pass

class GrandChildOfCharField(ChildOfCharField):
    pass
