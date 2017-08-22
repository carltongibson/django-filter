
from __future__ import absolute_import

from copy import deepcopy

from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_filters import filterset

from .. import compat, utils
from .filters import BooleanFilter, IsoDateTimeFilter

FILTER_FOR_DBFIELD_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
FILTER_FOR_DBFIELD_DEFAULTS.update({
    models.DateTimeField: {'filter_class': IsoDateTimeFilter},
    models.BooleanField: {'filter_class': BooleanFilter},
})


class FilterSet(filterset.FilterSet):
    FILTER_DEFAULTS = FILTER_FOR_DBFIELD_DEFAULTS

    @property
    def form(self):
        form = super(FilterSet, self).form

        if compat.is_crispy():
            from crispy_forms.helper import FormHelper
            from crispy_forms.layout import Layout, Submit

            layout_components = list(form.fields.keys()) + [
                Submit('', _('Submit'), css_class='btn-default'),
            ]
            helper = FormHelper()
            helper.form_method = 'GET'
            helper.template_pack = 'bootstrap3'
            helper.layout = Layout(*layout_components)

            form.helper = helper

        return form

    @property
    def qs(self):
        from rest_framework.exceptions import ValidationError

        try:
            return super(FilterSet, self).qs
        except forms.ValidationError as e:
            raise ValidationError(utils.raw_validation(e))
