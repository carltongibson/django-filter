from copy import deepcopy

from django import forms
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.related import RelatedObject
from django.db.models.sql.constants import LOOKUP_SEP
from django.utils.datastructures import SortedDict
from django.utils.text import capfirst

from django_filters.filters import Filter, CharFilter, BooleanFilter, \
    ChoiceFilter, DateFilter, DateTimeFilter, TimeFilter, ModelChoiceFilter, \
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
                filters = base.declared_filters.items() + filters

    return SortedDict(filters)

def get_model_field(model, f):
    parts = f.split(LOOKUP_SEP)
    opts = model._meta
    for name in parts[:-1]:
        try:
            rel = opts.get_field_by_name(name)[0]
        except FieldDoesNotExist:
            return None
        if isinstance(rel, RelatedObject):
            model = rel.model
            opts = rel.opts
        else:
            model = rel.rel.to
            opts = model._meta
    try:
        rel, model, direct, m2m = opts.get_field_by_name(parts[-1])
    except FieldDoesNotExist:
        return None
    if not direct:
        return rel.field.rel.to_field
    return rel

def filters_for_model(model, fields=None, exclude=None, filter_for_field=None):
    field_dict = SortedDict()
    opts = model._meta
    if fields is None:
        fields = [f.name for f in sorted(opts.fields + opts.many_to_many)]
    for f in fields:
        if exclude is not None and f in exclude:
            continue
        field = get_model_field(model, f)
        if field is None:
            field_dict[f] = None
            continue
        filter_ = filter_for_field(field, f)
        if filter_:
            field_dict[f] = filter_
    return field_dict

class FilterSetOptions(object):
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)

        self.order_by = getattr(options, 'order_by', False)

        self.form = getattr(options, 'form', forms.Form)

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

        if None in filters.values():
            raise TypeError("Meta.fields contains a field that isn't defined "
                "on this FilterSet")

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
    models.PositiveIntegerField: {
        'filter_class': NumberFilter,
    },
    models.PositiveSmallIntegerField: {
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
    },
    models.EmailField: {
        'filter_class': CharFilter,
    },
    models.FilePathField: {
        'filter_class': CharFilter,
    },
    models.URLField: {
        'filter_class': CharFilter,
    },
    models.XMLField: {
        'filter_class': CharFilter,
    },
    models.IPAddressField: {
        'filter_class': CharFilter,
    },
    models.CommaSeparatedIntegerField: {
        'filter_class': CharFilter,
    },
}

class BaseFilterSet(object):
    filter_overrides = {}

    def __init__(self, data=None, queryset=None, prefix=None):
        self.is_bound = data is not None
        self.data = data or {}
        if queryset is None:
            queryset = self._meta.model._default_manager.all()
        self.queryset = queryset
        self.form_prefix = prefix

        self.filters = deepcopy(self.base_filters)
        # propagate the model being used through the filters
        for filter_ in self.filters.values():
            filter_.model = self._meta.model

    def __iter__(self):
        for obj in self.qs:
            yield obj

    @property
    def qs(self):
        if not hasattr(self, '_qs'):
            qs = self.queryset.all()
            for name, filter_ in self.filters.iteritems():
                try:
                    if self.is_bound:
                        data = self.form[name].data
                    else:
                        data = self.form.initial.get(name, self.form[name].field.initial)
                    val = self.form.fields[name].clean(data)
                    qs = filter_.filter(qs, val)
                except forms.ValidationError:
                    pass
            if self._meta.order_by:
                try:
                    value = self.form.fields[ORDER_BY_FIELD].clean(self.form[ORDER_BY_FIELD].data)
                    if value:
                        qs = qs.order_by(value)
                except forms.ValidationError:
                    pass
            self._qs = qs
        return self._qs

    @property
    def form(self):
        if not hasattr(self, '_form'):
            fields = SortedDict([(name, filter_.field) for name, filter_ in self.filters.iteritems()])
            fields[ORDER_BY_FIELD] = self.ordering_field
            Form =  type('%sForm' % self.__class__.__name__, (self._meta.form,), fields)
            if self.is_bound:
                self._form = Form(self.data, prefix=self.form_prefix)
            else:
                self._form = Form(prefix=self.form_prefix)
        return self._form

    def get_ordering_field(self):
        if self._meta.order_by:
            if isinstance(self._meta.order_by, (list, tuple)):
                choices = [(f, capfirst(f)) for f in self._meta.order_by]
            else:
                choices = [(f, capfirst(f)) for f in self.filters]
            return forms.ChoiceField(label="Ordering", required=False, choices=choices)

    @property
    def ordering_field(self):
        if not hasattr(self, '_ordering_field'):
            self._ordering_field = self.get_ordering_field()
        return self._ordering_field

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
