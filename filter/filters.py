from django import forms

class Filter(object):
    creation_counter = 0
    field = forms.Field
    
    def __init__(self, label=None, widget=None, action=None):
        self.label = label
        self.field = self.field(label=label, widget=widget)
        self.action = action
        
        self.creation_counter = Filter.creation_counter
        Filter.creation_counter += 1
    
    def filter(self, qs, name, value):
        raise NotImplementedError

class CharFilter(Filter):
    field = forms.CharField
    
    def filter(self, qs, name, value):
        if self.action is not None:
            return self.action(qs, value)
        return qs.filter(**{name: value})
