
from __future__ import absolute_import
from copy import deepcopy

from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_filters import filterset
from .filters import BooleanFilter, IsoDateTimeFilter
from .. import compat

if compat.is_crispy:
    from crispy_forms.helper import FormHelper
    from crispy_forms.layout import Layout, Submit


FILTER_FOR_DBFIELD_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
FILTER_FOR_DBFIELD_DEFAULTS.update({
    models.DateTimeField: {'filter_class': IsoDateTimeFilter},
    models.BooleanField: {'filter_class': BooleanFilter},
})


class FilterSet(filterset.FilterSet):
    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS

    def __init__(self, *args, **kwargs):
        super(FilterSet, self).__init__(*args, **kwargs)

        if compat.is_crispy:
            layout_components = list(self.form.fields.keys()) + [
                Submit('', _('Submit'), css_class='btn-default'),
            ]
            helper = FormHelper()
            helper.form_method = 'GET'
            helper.template_pack = 'bootstrap3'
            helper.layout = Layout(*layout_components)

            self.form.helper = helper
