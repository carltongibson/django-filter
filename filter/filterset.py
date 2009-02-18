from copy import deepcopy

from django import forms
from django.db import models
from django.utils.datastructures import SortedDict
from django.utils.text import capfirst

from filter.filters import Filter, CharFilter, BooleanFilter, ChoiceFilter, \
    DateFilter, DateTimeFilter, TimeFilter, ModelChoiceFilter, \
    ModelMultipleChoiceFilter, NumberFilter

ORDER_BY_FIELD = 'o'

def get_declared_filters(bases, attrs, with_base_filters=True):
    filters = []
    for filter_name, obj in attrs.items():
        if isinstance(obj, Filter):
            obj = attrs.pop(filter_name)
            if getattr(obj, 'name', None) is None:
                obj.name = filter_name
            filters.append((filter_name, obj))
    filters.sort(key=lambda x: x[1].creation_counter)
    
    if with_base_filters:
        for base in bases[::-1]:
            if hasattr(base, 'base_filters'):
                filters = base.base_filters.items() + filters
    else:
        for base in bases[::-1]:
            if hasattr(base, 'declared_filters'):
                filters = base.declared_fields.items() + filters
    
    return SortedDict(filters)

def filters_for_model(model, fields=None, exclude=None, filter_for_field=None):
    field_list = []
    opts = model._meta
    for f in opts.fields + opts.many_to_many:
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        filter_ = filter_for_field(f, f.name)
        if filter_:
            field_list.append((f.name, filter_))
    return SortedDict(field_list)

class FilterSetOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)
        
        self.order_by = getattr(options, 'order_by', False)

class FilterSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, FilterSet)]
        except NameError:
            # We are defining FilterSet itself here
            parents = None
        declared_filters = get_declared_filters(bases, attrs, False)
        new_class = super(FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)
        
        if not parents:
            return new_class
        
        opts = new_class._meta = FilterSetOptions(getattr(new_class, 'Meta', None))
        if opts.model:
            filters = filters_for_model(opts.model, opts.fields, opts.exclude, new_class.filter_for_field)
            filters.update(declared_filters)
        else:
            filters = declared_filters
        
        new_class.declared_filters = declared_filters
        new_class.base_filters = filters
        return new_class

FILTER_FOR_DBFIELD_DEFAULTS = {
    models.CharField: {
        'filter_class': CharFilter
    },
    models.TextField: {
        'filter_class': CharFilter
    },
    models.BooleanField: {
        'filter_class': BooleanFilter
    },
    models.DateField: {
        'filter_class': DateFilter
    },
    models.DateTimeField: {
        'filter_class': DateTimeFilter
    },
    models.TimeField: {
        'filter_class': TimeFilter
    },
    models.OneToOneField: {
        'filter_class': ModelChoiceFilter,
        'extra': lambda f: {
            'queryset': f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to),
            'to_field_name': f.rel.field_name,
        }
    },
    models.ForeignKey: {
        'filter_class': ModelChoiceFilter, 
        'extra': lambda f: {
            'queryset': f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to),
            'to_field_name': f.rel.field_name
        }
    },
    models.ManyToManyField: {
        'filter_class': ModelMultipleChoiceFilter,
        'extra': lambda f: {
            'queryset': f.rel.to._default_manager.complex_filter(f.rel.limit_choices_to),
        }
    },
    models.DecimalField: {
        'filter_class': NumberFilter,
    },
    models.SmallIntegerField: {
        'filter_class': NumberFilter,
    },
    models.IntegerField: {
        'filter_class': NumberFilter,
    },
    models.FloatField: {
        'filter_class': NumberFilter,
    },
    models.NullBooleanField: {
        'filter_class': BooleanFilter,
    },
    models.SlugField: {
        'filter_class': CharFilter,
    }
}

class BaseFilterSet(object):
    filter_overrides = {}
    
    def __init__(self, data=None, queryset=None):
        self.data = data or {}
        self.queryset = queryset or self._meta.model._default_manager.all()
        
        self.filters = deepcopy(self.base_filters)
            
    def __iter__(self):
        for obj in self.qs:
            yield obj
    
    @property
    def qs(self):
        if not hasattr(self, '_qs'):            
            qs = self.queryset.all()
            for name, filter_ in self.filters.iteritems():
                try:
                    val = self.form.fields[name].clean(self.form[name].data)
                    qs = filter_.filter(qs, val)
                except forms.ValidationError:
                    pass
            if self._meta.order_by:
                try:
                    qs = qs.order_by(self.form.fields[ORDER_BY_FIELD].clean(self.form[ORDER_BY_FIELD].data))
                except forms.ValidationError:
                    pass
            self._qs = qs                
        return self._qs
    
    @property
    def form(self):
        if not hasattr(self, '_form'):
            fields = SortedDict([(f[0], f[1].field) for f in self.filters.iteritems()])
            if self._meta.order_by:
                if isinstance(self._meta.order_by, (list, tuple)):
                    choices = [(f, capfirst(f)) for f in self._meta.order_by]
                else:
                    choices = [(f, capfirst(f)) for f in self.filters]
                fields[ORDER_BY_FIELD] = forms.ChoiceField(label="Ordering", required=False, choices=choices)
            Form =  type('%sForm' % self.__class__.__name__, (forms.Form,), fields)
            self._form = Form(self.data)
        return self._form
        
    @classmethod
    def filter_for_field(cls, f, name):
        filter_for_field = dict(FILTER_FOR_DBFIELD_DEFAULTS, **cls.filter_overrides)

        default = {
            'name': name,
            'label': capfirst(f.verbose_name)
        }
        
        if f.choices:
            default['choices'] = f.choices
            return ChoiceFilter(**default)

        data = filter_for_field.get(f.__class__)
        if data is None:
            return
        filter_class = data.get('filter_class')
        default.update(data.get('extra', lambda f: {})(f))
        if filter_class is not None:
            return filter_class(**default)

class FilterSet(BaseFilterSet):
    __metaclass__ = FilterSetMetaclass
    
