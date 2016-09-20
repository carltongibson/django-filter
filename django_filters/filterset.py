from __future__ import absolute_import
from __future__ import unicode_literals

import copy
from collections import OrderedDict

from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import ForeignObjectRel
from django.utils import six
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from .compat import remote_field, remote_queryset
from .filters import (Filter, CharFilter, BooleanFilter, BaseInFilter, BaseRangeFilter,
                      ChoiceFilter, DateFilter, DateTimeFilter, TimeFilter, ModelChoiceFilter,
                      ModelMultipleChoiceFilter, NumberFilter, UUIDFilter,
                      DurationFilter, OrderingFilter)
from .utils import try_dbfield, get_all_model_fields, get_model_field, resolve_field, pretty_name, deprecate


ORDER_BY_FIELD = 'o'


class STRICTNESS(object):
    """
    Values of False & True chosen for backward compatability reasons.
    Originally, these were the only options.
    """
    IGNORE = False
    RETURN_NO_RESULTS = True
    RAISE_VALIDATION_ERROR = "RAISE"


def get_declared_filters(bases, attrs, with_base_filters=True):
    filters = []
    for filter_name, obj in list(attrs.items()):
        if isinstance(obj, Filter):
            obj = attrs.pop(filter_name)
            if getattr(obj, 'name', None) is None:
                obj.name = filter_name
            filters.append((filter_name, obj))
    filters.sort(key=lambda x: x[1].creation_counter)

    if with_base_filters:
        for base in bases[::-1]:
            if hasattr(base, 'base_filters'):
                filters = list(base.base_filters.items()) + filters
    else:
        for base in bases[::-1]:
            if hasattr(base, 'declared_filters'):
                filters = list(base.declared_filters.items()) + filters

    return OrderedDict(filters)


def filters_for_model(model, fields=None, exclude=None, filter_for_field=None,
                      filter_for_reverse_field=None):
    field_dict = OrderedDict()

    # Setting exclude with no fields implies all other fields.
    if exclude is not None and fields is None:
        fields = '__all__'

    # All implies all db fields associated with a filter_class.
    if fields == '__all__':
        fields = get_all_model_fields(model)

    # Loop through the list of fields.
    for f in fields:
        # Skip the field if excluded.
        if exclude is not None and f in exclude:
            continue
        field = get_model_field(model, f)
        # Do nothing if the field doesn't exist.
        if field is None:
            field_dict[f] = None
            continue
        if isinstance(field, ForeignObjectRel):
            filter_ = filter_for_reverse_field(field, f)
            if filter_:
                field_dict[f] = filter_
        # If fields is a dictionary, it must contain lists.
        elif isinstance(fields, dict):
            # Create a filter for each lookup type.
            for lookup_expr in fields[f]:
                filter_ = filter_for_field(field, f, lookup_expr)

                if filter_:
                    filter_name = LOOKUP_SEP.join([f, lookup_expr])

                    # Don't add "exact" to filter names
                    _exact = LOOKUP_SEP + 'exact'
                    if filter_name.endswith(_exact):
                        filter_name = filter_name[:-len(_exact)]

                    field_dict[filter_name] = filter_
        # If fields is a list, it contains strings.
        else:
            filter_ = filter_for_field(field, f)
            if filter_:
                field_dict[f] = filter_
    return field_dict


def get_full_clean_override(together):
    def full_clean(form):

        def add_error(message):
            try:
                form.add_error(None, message)
            except AttributeError:
                form._errors[NON_FIELD_ERRORS] = message

        def all_valid(fieldset):
            cleaned_data = form.cleaned_data
            count = len([i for i in fieldset if cleaned_data.get(i)])
            return 0 < count < len(fieldset)

        super(form.__class__, form).full_clean()
        message = 'Following fields must be together: %s'
        if isinstance(together[0], (list, tuple)):
            for each in together:
                if all_valid(each):
                    return add_error(message % ','.join(each))
        elif all_valid(together):
            return add_error(message % ','.join(together))
    return full_clean


class FilterSetOptions(object):
    def __init__(self, options=None):
        if getattr(options, 'model', None) is not None:
            if not hasattr(options, 'fields') and not hasattr(options, 'exclude'):
                deprecate(
                    "Not setting Meta.fields with Meta.model is undocumented behavior "
                    "and may result in unintentionally exposing filter fields. This has "
                    "been deprecated in favor of setting Meta.fields = '__all__' or by "
                    "setting the Meta.exclude attribute.", 1)

            elif getattr(options, 'fields', -1) is None:
                deprecate(
                    "Setting 'Meta.fields = None' is undocumented behavior and has been "
                    "deprecated in favor of Meta.fields = '__all__'.", 1)

        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)

        self.filter_overrides = getattr(options, 'filter_overrides', {})

        if hasattr(options, 'order_by'):
            deprecate('Meta.order_by has been deprecated.', 1)

        if hasattr(options, 'order_by_field'):
            deprecate('Meta.order_by_field has been deprecated.', 1)

        self.order_by = getattr(options, 'order_by', False)
        self.order_by_field = getattr(options, 'order_by_field', ORDER_BY_FIELD)

        self.strict = getattr(options, 'strict', STRICTNESS.RETURN_NO_RESULTS)

        self.form = getattr(options, 'form', forms.Form)

        self.together = getattr(options, 'together', None)


class FilterSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        try:
            parents = [b for b in bases if issubclass(b, FilterSet)]
        except NameError:
            # We are defining FilterSet itself here
            parents = None
        declared_filters = get_declared_filters(bases, attrs, False)
        new_class = super(
            FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)

        if not parents:
            return new_class

        opts = new_class._meta = FilterSetOptions(
            getattr(new_class, 'Meta', None))

        if hasattr(new_class, 'strict'):
            deprecate('strict has been deprecated. Use Meta.strict instead.')
            new_class._meta.strict = new_class.strict

        if hasattr(new_class, 'order_by_field'):
            deprecate('order_by_field has been moved to the Meta class.')
            new_class._meta.order_by_field = new_class.order_by_field

        if hasattr(new_class, 'filter_overrides'):
            deprecate('filter_overrides has been moved to the Meta class.')
            new_class._meta.filter_overrides = new_class.filter_overrides

        assert not hasattr(new_class, 'get_order_by'), \
            'get_order_by() has been deprecated. Subclass OrderingFilter and override .filter() instead. ' \
            'See: https://django-filter.readthedocs.io/en/latest/migration.html"'

        assert not hasattr(new_class, 'get_ordering_field'), \
            'get_ordering_field() has been deprecated. Use OrderingFilter instead. ' \
            'See: https://django-filter.readthedocs.io/en/latest/migration.html"'

        # TODO: replace with deprecations
        # if opts.model and opts.fields:
        if opts.model:
            filters = new_class.filters_for_model(opts.model, opts)
            filters.update(declared_filters)
        else:
            filters = declared_filters

        not_defined = next((k for k, v in filters.items() if v is None), False)
        if not_defined:
            raise TypeError("Meta.fields contains a field that isn't defined "
                            "on this FilterSet: {}".format(not_defined))

        # TODO: remove with deprecations
        # check key existence instead of setdefault - prevents unnecessary filter construction
        order_by_field = new_class._meta.order_by_field
        if opts.order_by and order_by_field not in filters:
            filters[order_by_field] = new_class.get_ordering_filter(opts, filters)

        new_class.declared_filters = declared_filters
        new_class.base_filters = filters
        return new_class


FILTER_FOR_DBFIELD_DEFAULTS = {
    models.AutoField:                   {'filter_class': NumberFilter},
    models.CharField:                   {'filter_class': CharFilter},
    models.TextField:                   {'filter_class': CharFilter},
    models.BooleanField:                {'filter_class': BooleanFilter},
    models.DateField:                   {'filter_class': DateFilter},
    models.DateTimeField:               {'filter_class': DateTimeFilter},
    models.TimeField:                   {'filter_class': TimeFilter},
    models.DurationField:               {'filter_class': DurationFilter},
    models.DecimalField:                {'filter_class': NumberFilter},
    models.SmallIntegerField:           {'filter_class': NumberFilter},
    models.IntegerField:                {'filter_class': NumberFilter},
    models.PositiveIntegerField:        {'filter_class': NumberFilter},
    models.PositiveSmallIntegerField:   {'filter_class': NumberFilter},
    models.FloatField:                  {'filter_class': NumberFilter},
    models.NullBooleanField:            {'filter_class': BooleanFilter},
    models.SlugField:                   {'filter_class': CharFilter},
    models.EmailField:                  {'filter_class': CharFilter},
    models.FilePathField:               {'filter_class': CharFilter},
    models.URLField:                    {'filter_class': CharFilter},
    models.GenericIPAddressField:       {'filter_class': CharFilter},
    models.CommaSeparatedIntegerField:  {'filter_class': CharFilter},
    models.UUIDField:                   {'filter_class': UUIDFilter},
    models.OneToOneField: {
        'filter_class': ModelChoiceFilter,
        'extra': lambda f: {
            'queryset': remote_queryset(f),
            'to_field_name': remote_field(f).field_name,
        }
    },
    models.ForeignKey: {
        'filter_class': ModelChoiceFilter,
        'extra': lambda f: {
            'queryset': remote_queryset(f),
            'to_field_name': remote_field(f).field_name,
        }
    },
    models.ManyToManyField: {
        'filter_class': ModelMultipleChoiceFilter,
        'extra': lambda f: {
            'queryset': remote_queryset(f),
        }
    },
}


class BaseFilterSet(object):
    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS

    def __init__(self, data=None, queryset=None, prefix=None, strict=None):
        self.is_bound = data is not None
        self.data = data or {}
        if queryset is None:
            queryset = self._meta.model._default_manager.all()
        self.queryset = queryset
        self.form_prefix = prefix

        # What to do on on validation errors
        self.strict = self._meta.strict if strict is None else strict

        self.filters = copy.deepcopy(self.base_filters)
        # propagate the model being used through the filters
        for filter_ in self.filters.values():
            filter_.model = self._meta.model

        # Apply the parent to the filters, this will allow the filters to access the filterset
        for filter_key, filter_ in six.iteritems(self.filters):
            filter_.parent = self

    def __iter__(self):
        deprecate('QuerySet methods are no longer proxied.')
        for obj in self.qs:
            yield obj

    def __len__(self):
        deprecate('QuerySet methods are no longer proxied.')
        return self.qs.count()

    def __getitem__(self, key):
        deprecate('QuerySet methods are no longer proxied.')
        return self.qs[key]

    def count(self):
        deprecate('QuerySet methods are no longer proxied.')
        return self.qs.count()

    @property
    def qs(self):
        if not hasattr(self, '_qs'):
            valid = self.is_bound and self.form.is_valid()

            if self.is_bound and not valid:
                if self.strict == STRICTNESS.RAISE_VALIDATION_ERROR:
                    raise forms.ValidationError(self.form.errors)
                elif bool(self.strict) == STRICTNESS.RETURN_NO_RESULTS:
                    self._qs = self.queryset.none()
                    return self._qs
                # else STRICTNESS.IGNORE...  ignoring

            # start with all the results and filter from there
            qs = self.queryset.all()
            for name, filter_ in six.iteritems(self.filters):
                value = None
                if valid:
                    value = self.form.cleaned_data[name]
                else:
                    raw_value = self.form[name].value()
                    try:
                        value = self.form.fields[name].clean(raw_value)
                    except forms.ValidationError:
                        if self.strict == STRICTNESS.RAISE_VALIDATION_ERROR:
                            raise
                        elif bool(self.strict) == STRICTNESS.RETURN_NO_RESULTS:
                            self._qs = self.queryset.none()
                            return self._qs
                        # else STRICTNESS.IGNORE...  ignoring

                if value is not None:  # valid & clean data
                    qs = filter_.filter(qs, value)

            self._qs = qs

        return self._qs

    @property
    def form(self):
        if not hasattr(self, '_form'):
            fields = OrderedDict([
                (name, filter_.field)
                for name, filter_ in six.iteritems(self.filters)])

            Form = type(str('%sForm' % self.__class__.__name__),
                        (self._meta.form,), fields)
            if self._meta.together:
                Form.full_clean = get_full_clean_override(self._meta.together)
            if self.is_bound:
                self._form = Form(self.data, prefix=self.form_prefix)
            else:
                self._form = Form(prefix=self.form_prefix)
        return self._form

    @classmethod
    def get_ordering_filter(cls, opts, filters):
        assert not isinstance(opts.fields, dict), \
            "'order_by' is not compatible with the 'fields' dict syntax. Use OrderingFilter instead."

        def display_text(name, fltr):
            """
            ``name`` is the filter's attribute name on the FilterSet
            ``text`` is the current display text, which is either the ``name``
                     or an explicitly assigned label.
            """
            # TODO: use `fltr._label` in label-improvements branch
            text = fltr.label or name.lstrip('-')
            if name.startswith('-'):
                text = _('%s (descending)' % text)

            return pretty_name(text)

        if isinstance(opts.order_by, (list, tuple)):

            # e.g. (('field', 'Display name'), ...)
            if isinstance(opts.order_by[0], (list, tuple)):
                choices = [(f[0], f[1]) for f in opts.order_by]
                fields = {filters.get(f[0].lstrip('-')).name: f[0] for f in opts.order_by}
                return OrderingFilter(choices=choices, fields=fields)

            # e.g. ('field1', 'field2', ...)
            else:
                # (filter name, filter instance)
                order_by = [(f, filters.get(f.lstrip('-'))) for f in opts.order_by]

                # preference filter label over attribute name
                choices = [(f, display_text(f, fltr)) for f, fltr in order_by]
                fields = {fltr.name: f for f, fltr in order_by}
                return OrderingFilter(choices=choices, fields=fields)

        # opts.order_by = True
        order_by = filters.items()

        fields = [(fltr.name, f) for f, fltr in order_by]
        labels = {f: display_text(f, fltr) for f, fltr in order_by}
        return OrderingFilter(fields=fields, field_labels=labels)

    @classmethod
    def filters_for_model(cls, model, opts):
        # TODO: remove with deprecations - this emulates the old behavior
        fields = opts.fields
        if fields is None:
            DEFAULTS = dict(FILTER_FOR_DBFIELD_DEFAULTS)
            DEFAULTS.update(opts.filter_overrides)
            fields = get_all_model_fields(model, field_types=DEFAULTS.keys())

        return filters_for_model(
            model, fields, opts.exclude,
            cls.filter_for_field,
            cls.filter_for_reverse_field
        )

    @classmethod
    def filter_for_field(cls, f, name, lookup_expr='exact'):
        f, lookup_type = resolve_field(f, lookup_expr)

        default = {
            'name': name,
            'label': capfirst(f.verbose_name),
            'lookup_expr': lookup_expr
        }

        filter_class, params = cls.filter_for_lookup(f, lookup_type)
        default.update(params)

        assert filter_class is not None, (
            "%s resolved field '%s' with '%s' lookup to an unrecognized field "
            "type %s. Try adding an override to 'filter_overrides'. See: "
            "https://django-filter.readthedocs.io/en/latest/usage.html#overriding-default-filters"
        ) % (cls.__name__, name, lookup_expr, f.__class__.__name__)

        return filter_class(**default)

    @classmethod
    def filter_for_reverse_field(cls, f, name):
        rel = remote_field(f.field)
        queryset = f.field.model._default_manager.all()
        default = {
            'name': name,
            'label': capfirst(rel.related_name),
            'queryset': queryset,
        }
        if rel.multiple:
            return ModelMultipleChoiceFilter(**default)
        else:
            return ModelChoiceFilter(**default)

    @classmethod
    def filter_for_lookup(cls, f, lookup_type):
        DEFAULTS = dict(cls.FILTER_DEFAULTS)
        if hasattr(cls, '_meta'):
            DEFAULTS.update(cls._meta.filter_overrides)

        data = try_dbfield(DEFAULTS.get, f.__class__) or {}
        filter_class = data.get('filter_class')
        params = data.get('extra', lambda f: {})(f)

        # if there is no filter class, exit early
        if not filter_class:
            return None, {}

        # perform lookup specific checks
        if lookup_type == 'exact' and f.choices:
            return ChoiceFilter, {'choices': f.choices}

        if lookup_type == 'isnull':
            data = try_dbfield(DEFAULTS.get, models.BooleanField)

            filter_class = data.get('filter_class')
            params = data.get('extra', lambda f: {})(f)
            return filter_class, params

        if lookup_type == 'in':
            class ConcreteInFilter(BaseInFilter, filter_class):
                pass
            ConcreteInFilter.__name__ = cls._csv_filter_class_name(
                filter_class, lookup_type
            )

            return ConcreteInFilter, params

        if lookup_type == 'range':
            class ConcreteRangeFilter(BaseRangeFilter, filter_class):
                pass
            ConcreteRangeFilter.__name__ = cls._csv_filter_class_name(
                filter_class, lookup_type
            )

            return ConcreteRangeFilter, params

        return filter_class, params

    @classmethod
    def _csv_filter_class_name(cls, filter_class, lookup_type):
        """
        Generate a suitable class name for a concrete filter class. This is not
        completely reliable, as not all filter class names are of the format
        <Type>Filter.

        ex::

            FilterSet._csv_filter_class_name(DateTimeFilter, 'in')

            returns 'DateTimeInFilter'

        """
        # DateTimeFilter => DateTime
        type_name = filter_class.__name__
        if type_name.endswith('Filter'):
            type_name = type_name[:-6]

        # in => In
        lookup_name = lookup_type.capitalize()

        # DateTimeInFilter
        return str('%s%sFilter' % (type_name, lookup_name))


class FilterSet(six.with_metaclass(FilterSetMetaclass, BaseFilterSet)):
    pass


def filterset_factory(model):
    meta = type(str('Meta'), (object,), {'model': model, 'fields': '__all__'})
    filterset = type(str('%sFilterSet' % model._meta.object_name),
                     (FilterSet,), {'Meta': meta})
    return filterset
