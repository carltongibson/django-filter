from django.utils.datastructures import SortedDict

from filter.filters import Filter

def get_declared_filters(bases, attrs, with_base_filters=True):
    filters = [(filter_name, attrs.pop(filter_name)) for filter_name, obj in attrs.iteritems() if isinstance(obj, Filter)]
    filters.sort(key=lambda x: x.creation_counter)
    
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
        filter_ = filter_for_field(f)
        if filter_:
            field_list.append((f.name, filter_))
    return SortedDict(field_list)

class FilterSetOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)

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

class BaseFilterSet(object):
    def __init__(self, data):
        self.data = data
        
    @classmethod
    def filter_for_field(cls, f):
        from django.db import models
        FILTERS = {
            models.CharField: Filter,
        }
        return FILTERS.get(f.__class__)

class FilterSet(BaseFilterSet):
    __metaclass__ = FilterSetMetaclass
    
