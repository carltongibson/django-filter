from django import forms

__all__ = ['Filter', 'CharFilter', 'BooleanFilter']

class Filter(object):
    creation_counter = 0
    field = forms.Field
    
    def __init__(self, name=None, label=None, widget=None, action=None):
        self.name = name
        self.label = label
        self.field = self.field(label=label, widget=widget)
        if action:
            self.filter = action
        
        self.creation_counter = Filter.creation_counter
        Filter.creation_counter += 1
    
    def filter(self, qs, value):
        if value:
            return qs.filter(**{self.name: value})
        return qs
    
class CharFilter(Filter):
    field = forms.CharField

class BooleanFilter(Filter):
    field = forms.BooleanField
