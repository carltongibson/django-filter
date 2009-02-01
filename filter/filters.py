from django import forms
from django.db.models import Q

__all__ = [
    'Filter', 'CharFilter', 'BooleanFilter', 'ChoiceFilter', 
    'MultipleChoiceFilter', 'DateFilter', 'DateTimeFilter', 'TimeFilter', 
    'ModelChoiceFilter', 'ModelMultipleChoiceFilter', 'NumberFilter'
]

class Filter(object):
    creation_counter = 0
    field = forms.Field
    
    def __init__(self, name=None, label=None, widget=None, action=None, 
        lookup_type='exact', **kwargs):
        self.name = name
        self.label = label
        self.field = self.field(required=False, label=label, widget=widget, **kwargs)
        if action:
            self.filter = action
        self.lookup_type = lookup_type
        
        self.extra = kwargs
        
        self.creation_counter = Filter.creation_counter
        Filter.creation_counter += 1
    
    def filter(self, qs, value):
        if value:
            return qs.filter(**{'%s__%s' % (self.name, self.lookup_type): value})
        return qs
        
class CharFilter(Filter):
    field = forms.CharField

class BooleanFilter(Filter):
    field = forms.NullBooleanField
    
    def filter(self, qs, value):
        if value is not None:
            return qs.filter(**{self.name: value})
        return qs

class ChoiceFilter(Filter):
    field = forms.ChoiceField

class MultipleChoiceFilter(Filter):
    """
    This filter preforms an OR query on the selected options.
    """
    field = forms.MultipleChoiceField
    
    def filter(self, qs, value):
        q = Q()
        for v in value:
            q |= Q(**{self.name: v})
        return qs.filter(q).distinct()

class DateFilter(Filter):
    field = forms.DateField

class DateTimeFilter(Filter):
    field = forms.DateTimeField

class TimeFilter(Filter):
    field = forms.TimeField

class ModelChoiceFilter(Filter):
    field = forms.ModelChoiceField

class ModelMultipleChoiceFilter(MultipleChoiceFilter):
    field = forms.ModelMultipleChoiceField

class NumberFilter(Filter):
    field = forms.DecimalField
