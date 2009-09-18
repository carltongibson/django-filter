from django.shortcuts import render_to_response
from django.template import RequestContext

from django_filters.filterset import FilterSet

def object_filter(request, model=None, queryset=None, template_name=None, extra_context=None,
    context_processors=None, filter_class=None):
    if model is None and filter_class is None:
        raise TypeError("object_filter must be called with either model or filter_class")
    if model is None:
        model = filter_class._meta.model
    if filter_class is None:
        meta = type('Meta', (object,), {'model': model})
        filter_class = type('%sFilterSet' % model._meta.object_name, (FilterSet,),
            {'Meta': meta})
    filterset = filter_class(request.GET or None, queryset=queryset)

    if not template_name:
        template_name = '%s/%s_filter.html' % (model._meta.app_label, model._meta.object_name.lower())
    c = RequestContext(request, {
        'filter': filterset,
    })
    if extra_context:
        for k, v in extra_context.iteritems():
            if callable(v):
                v = v()
            c[k] = v
    return render_to_response(template_name, c)
