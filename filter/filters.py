from django import forms
from django.db.models import Q

__all__ = ['Filter', 'CharFilter', 'BooleanFilter', 'ChoiceFilter', 'MultipleChoiceFilter']

class Filter(object):
    creation_counter = 0
    field = forms.Field
    
    def __init__(self, name=None, label=None, widget=None, action=None, **kwargs):
        self.name = name
        self.label = label
        self.field = self.field(required=False, label=label, widget=widget, **kwargs)
        if action:
            self.filter = action
        
        self.creation_counter = Filter.creation_counter
        Filter.creation_counter += 1
    
    def filter(self, qs, value):
        return qs.filter(**{self.name: value})
        
class CharFilter(Filter):
    field = forms.CharField

class BooleanFilter(Filter):
    field = forms.BooleanField

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
        return qs.filter(q)
