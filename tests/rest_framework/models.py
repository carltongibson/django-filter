
from django.db import models
from django.utils.translation import ugettext_lazy as _


class BasicModel(models.Model):
    text = models.CharField(
        max_length=100,
        verbose_name=_("Text comes here"),
        help_text=_("Text description.")
    )


class BaseFilterableItem(models.Model):
    text = models.CharField(max_length=100)


class FilterableItem(BaseFilterableItem):
    decimal = models.DecimalField(max_digits=4, decimal_places=2)
    date = models.DateField()


class DjangoFilterOrderingModel(models.Model):
    date = models.DateField()
    text = models.CharField(max_length=10)

    class Meta:
        ordering = ['-date']
