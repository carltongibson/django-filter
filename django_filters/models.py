### these models are for testing

from django.db import models

STATUS_CHOICES = (
    (0, 'Regular'),
    (1, 'Admin'),
)

class User(models.Model):
    username = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    status = models.IntegerField(choices=STATUS_CHOICES, default=0)

    is_active = models.BooleanField()

    favorite_books = models.ManyToManyField('Book')

    def __unicode__(self):
        return self.username

class Comment(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User)

    date = models.DateField()
    time = models.TimeField()

    def __unicode__(self):
        return "%s said %s" % (self.author, self.text[:25])

class Article(models.Model):
    published = models.DateTimeField()

class Book(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    average_rating = models.FloatField()

    def __unicode__(self):
        return self.title

class Place(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        abstract = True

class Restaurant(Place):
    serves_pizza = models.BooleanField()
