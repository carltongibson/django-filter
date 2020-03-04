import functools
import operator
from abc import abstractmethod

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP
from django.utils.translation import ugettext as _

from .constants import EMPTY_VALUES

__all__ = [
    'BaseFilterGroup', 'ExclusiveGroup', 'RequiredGroup',
    'CombinedGroup', 'CombinedRequiredGroup',
]


class BaseFilterGroup:
    """Base class for validating & filtering query parameters as a group."""

    def __init__(self, filters):
        if not filters or len(filters) < 2:
            msg = "A filter group must contain at least two members."
            raise ValueError(msg)
        if len(set(filters)) != len(filters):
            msg = "A filter group must not contain duplicate members."
            raise ValueError(msg)
        self.filters = filters

        # Set during parent FilterSet initialization
        self.parent = None
        self.model = None

    @abstractmethod
    def validate(self, form, **data):
        """Validate the subset of cleaned data provided by the form.

        Args:
            form: The underlying ``Form`` instance used to validate the query
                params. A ``FilterGroup`` should add errors to this form using
                ``form.add_error(<field name>, <error message>)``.
            **data: The subset of a form's ``cleaned_data`` for the filters in
                the group.
        """
        raise NotImplementedError

    @abstractmethod
    def filter(self, qs, **data):
        """Filter the result queryset with the subset of cleaned data.

        Args:
            qs: The ``QuerySet`` instance to filter.
            **data: The subset of a form's ``cleaned_data`` for the filters in
                the group.

        Returns:
            The filtered queryset instance.
        """
        raise NotImplementedError

    def format_labels(self, filters):
        """Return a formatted string of labels for the given filter names.

        This inspects the filter labels from the ``self.parent`` FilterSet,
        and combines them into a formatted string. This string can then be
        used in validation error messages.

        Args:
            filters: A list of filter names.

        Returns:
            The formatted string of labels. For example, if filters 'a', 'b',
            and 'c' have corresponding labels 'Filter A', 'Filter B', and
            'Filter C', then...

            >>> group.format_labels(['a', 'b'])
            "'Filter A' and 'Filter B'"

            >>> group.format_labels(['a', 'b', 'c'])
            "'Filter A', 'Filter B', and 'Filter C'"
        """
        labels = [self.parent.filters[name].label for name in filters]

        if len(labels) == 2:
            return "'%s' and '%s'" % tuple(labels)

        # e.g., joined = "'A', 'B', and 'C'"
        joined = ', '.join("'%s'" % l for l in labels)
        joined = ', and '.join(joined.rsplit(', ', 1))
        return joined

    def extract_data(self, cleaned_data):
        """Extract the subset of cleaned data for the filters in the group.

        Note that this is an internal method called by the ``FilterSet``.
        Subclasses should not need to call or override this method.

        Args:
            cleaned_data: The underlying form's ``cleaned_data`` dict.

        Returns:
            A two-tuple containing the dict subset of data for the filters in
            the group, and the remainder of the original ``cleaned_data`` dict.
        """
        # Create a copy so as to not modify the original data dict.
        data = cleaned_data.copy()

        return {
            name: data.pop(name)
            for name in self.filters
            if name in data
        }, data

    def _filter_data(self, data):
        # Helper for checking the extacted data.
        # - Sanity check that correct data has been provided by the filterset.
        # - Remove empty values that would normally be skipped by the
        #     ``Filter.filter`` method.
        assert set(data).issubset(set(self.filters)), (
            "The `data` must be a subset of the group's `.filters`.")
        return {k: v for k, v in data.items() if v not in EMPTY_VALUES}


class ExclusiveGroup(BaseFilterGroup):
    """A group of mutually exclusive filters.

    If any filter in the group is included in the request data, then all other
    filters in the group **must not** be present in the request data.

    Attributes:
        filters: The set of filter names to operate on.
    """

    def validate(self, form, **data):
        data = self._filter_data(data)

        if len(data) > 1:
            err = ValidationError(
                _('%(filters)s are mutually exclusive.'),
                params={'filters': self.format_labels(self.filters)})

            # The error message should include all filters (A, B, and C),
            # but the error should only be raised for the given filters.
            for param in data:
                form.add_error(param, err)

    def filter(self, qs, **data):
        data = self._filter_data(data)
        if not data:
            return qs

        assert len(data) <= 1, "The `data` should consist of only one element."

        param, value = next(iter(data.items()))

        return self.parent.filters[param].filter(qs, value)


class RequiredGroup(BaseFilterGroup):
    """A group of mutually required filters.

    If any filter in the group is included in the request data, then all other
    filters in the group **must** be present in the request data. Filtering is
    still performed by the individual filters and is not combined via ``Q``
    objects. To use ``Q`` objects instead (e.g., for OR-based filtering), use
    the ``CombinedRequiredGroup``.

    Attributes:
        filters: The set of filter names to operate on.
    """

    def validate(self, form, **data):
        data = self._filter_data(data)

        if data and set(data) != set(self.filters):
            err = ValidationError(
                _('%(filters)s are mutually required.'),
                params={'filters': self.format_labels(self.filters)})

            # Unlike ``ExclusiveGroup``, the error should be raised for all
            # filters since the missing filters are part of the error state.
            for param in self.filters:
                form.add_error(param, err)

    def filter(self, qs, **data):
        data = self._filter_data(data)

        assert not data or len(data) == len(self.filters), (
            "The `data` should contain all filters.")

        # Filter by chaining the original filter method calls.
        for param, value in data.items():
            qs = self.parent.filters[param].filter(qs, value)

        return qs


class CombinedGroup(BaseFilterGroup):
    """A group of filters that result in a combined query (a ``Q`` object).

    This implementation combines ``Q`` objects *instead* of chaining
    ``.filter()`` calls. The ``Q`` objects are generated from the filter's
    ``field_name``, ``lookup_expr``, and ``exclude`` attributes, and the
    resulting queryset will call ``.distinct()`` if set on any of the filters.

    In short, instead of generating the following filter call:

    .. code-block:: python

        qs.filter(a=1).filter(b=2)

    This group would generate a call like:

    .. code-block:: python

        qs.filter(Q(a=1) & Q(b=2))

    This is useful for enabling OR filtering, as well as combining filters that
    span multi-valued relationships (`more info`__).

    __ https://docs.djangoproject.com/en/stable/topics/db/queries/#spanning-multi-valued-relationships

    Attributes:
        filters: The set of filter names to operate on.
        combine: A function that combines two ``Q`` objects. Defaults to
            ``operator.and_``. For OR operations, use ``operator.or_``.
    """

    def __init__(self, filters, combine=operator.and_):
        super().__init__(filters)
        self.combine = combine

    def validate(self, form, **data):
        # CombinedGroup has no specific validation rules.
        self._filter_data(data)

    def filter(self, qs, **data):
        data = self._filter_data(data)

        if not data:
            return qs

        # Filter by combining the set of constructed Q objects.
        qs = qs.filter(functools.reduce(self.combine, [
            self.build_q_object(param, value)
            for param, value in data.items()]))

        # If any filter is marked as distinct, the qs should also be distinct.
        if any(self.parent.filters[param].distinct for param in data):
            qs = qs.distinct()

        return qs

    def build_q_object(self, filter_name, value):
        """Build a ``Q`` object for the given filter name and value.

        The ``Q`` objects are generated from the filter's ``field_name``,
        ``lookup_expr``, and ``exclude`` attributes.

        Args:
            filter_name: The name of the filter to base the ``Q`` object off of.
            value: The value to filter within the ``Q`` object.

        Returns:
            A ``Q`` object that is reprentative of the filter and value.
        """
        f = self.parent.filters[filter_name]
        q = Q(**{LOOKUP_SEP.join([f.field_name, f.lookup_expr]): value})
        if f.exclude:
            q = ~q

        return q


class CombinedRequiredGroup(CombinedGroup, RequiredGroup):
    """A group of mutually required filters that result in a combined query.

    This combines the validation logic of a ``RequiredGroup`` with the
    filtering logic of a ``CombinedGroup``.

    Attributes:
        filters: The set of filter names to operate on.
        combine: A function that combines two ``Q`` objects. Defaults to
            ``operator.and_``. For OR operations, use ``operator.or_``.
    """

    def validate(self, form, **data):
        # Use the validation provided by RequiredGroup
        super(CombinedGroup, self).validate(form, **data)
