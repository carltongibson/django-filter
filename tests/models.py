from __future__ import absolute_import
from __future__ import unicode_literals

from django import forms
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


REGULAR = 0
MANAGER = 1
ADMIN = 2

STATUS_CHOICES = (
    (REGULAR, 'Regular'),
    (MANAGER, 'Manager'),
    (ADMIN, 'Admin'),
)


# classes for testing filters with inherited fields
class SubCharField(models.CharField):
    pass


class SubSubCharField(SubCharField):
    pass


class SubnetMaskField(models.Field):
    empty_strings_allowed = False
    description = "Subnet Mask"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 15
        models.Field.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "GenericIPAddressField"

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.GenericIPAddressField}
        defaults.update(kwargs)
        return super(SubnetMaskField, self).formfield(**defaults)


@python_2_unicode_compatible
class User(models.Model):
    username = models.CharField(max_length=255)
    first_name = SubCharField(max_length=100)
    last_name = SubSubCharField(max_length=100)

    status = models.IntegerField(choices=STATUS_CHOICES, default=0)

    is_active = models.BooleanField(default=False)

    favorite_books = models.ManyToManyField('Book', related_name='lovers')

    def __str__(self):
        return self.username


@python_2_unicode_compatible
class ManagerGroup(models.Model):
    users = models.ManyToManyField(User,
                                   limit_choices_to={'is_active': True},
                                   related_name='member_of')
    manager = models.ForeignKey(User,
                                limit_choices_to=lambda: {'status': MANAGER},
                                related_name='manager_of',
                                on_delete=models.CASCADE)

    def __str__(self):
        return self.manager.name + ' group'


@python_2_unicode_compatible
class AdminUser(User):
    class Meta:
        proxy = True

    def __str__(self):
        return "%s (ADMIN)" % self.username


@python_2_unicode_compatible
class Comment(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)

    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return "%s said %s" % (self.author, self.text[:25])


class Article(models.Model):
    published = models.DateTimeField()
    author = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    def __str__(self):
        if self.author_id:
            return "%s on %s" % (self.author, self.published)
        return "Anonymous on %s" % self.published


@python_2_unicode_compatible
class Book(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    average_rating = models.FloatField()

    def __str__(self):
        return self.title


class Place(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        abstract = True


class Restaurant(Place):
    serves_pizza = models.BooleanField(default=False)


class NetworkSetting(models.Model):
    ip = models.GenericIPAddressField()
    mask = SubnetMaskField()


@python_2_unicode_compatible
class Company(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


@python_2_unicode_compatible
class Location(models.Model):
    company = models.ForeignKey(Company, related_name='locations', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    open_days = models.CharField(max_length=7)

    def __str__(self):
        return '%s: %s' % (self.company.name, self.name)


class Account(models.Model):
    name = models.CharField(max_length=100)
    in_good_standing = models.BooleanField(default=False)
    friendly = models.BooleanField(default=False)


class Profile(models.Model):
    account = models.OneToOneField(Account, related_name='profile', on_delete=models.CASCADE)
    likes_coffee = models.BooleanField(default=False)
    likes_tea = models.BooleanField(default=False)


class BankAccount(Account):
    amount_saved = models.IntegerField(default=0)


class Node(models.Model):
    name = models.CharField(max_length=20)
    adjacents = models.ManyToManyField('self')


class DirectedNode(models.Model):
    name = models.CharField(max_length=20)
    outbound_nodes = models.ManyToManyField('self',
                                            symmetrical=False,
                                            related_name='inbound_nodes')


class Worker(models.Model):
    name = models.CharField(max_length=100)


class HiredWorker(models.Model):
    salary = models.IntegerField()
    hired_on = models.DateField()
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    business = models.ForeignKey('Business', on_delete=models.CASCADE)


class Business(models.Model):
    name = models.CharField(max_length=100)
    employees = models.ManyToManyField(Worker,
                                       through=HiredWorker,
                                       related_name='employers')


class UUIDTestModel(models.Model):
    uuid = models.UUIDField()


class SpacewalkRecord(models.Model):
    """Cumulative space walk record.

    See: https://en.wikipedia.org/wiki/List_of_cumulative_spacewalk_records

    """
    astronaut = models.CharField(max_length=100)
    duration = models.DurationField()
