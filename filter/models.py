### these models are for testing

from django.db import models

class User(models.Model):
    username = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    is_active = models.BooleanField()
    
    def __unicode__(self):
        return self.username
