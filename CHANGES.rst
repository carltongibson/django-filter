Version 0.10.0 (2015-05-13)
---------------------

* FEATURE: Added ``conjoined`` parameter to ``MultipleChoiceFilter``

* FEATURE: Added ``together`` meta option to validate fields as a group

* FIXED: Added testing on Django 1.8

* FIXED: ``get_model_field`` on Django 1.8


Version 0.9.2 (2015-01-23)
--------------------------

* FIXED: Compatibility with Django v1.8a1

Version 0.9.1 (2014-12-03)
--------------------------

* FIXED: Compatibility with Debug Toolbar's versions panel

Version 0.9 (2014-11-28)
------------------------

* FEATURE: Allow Min/Max-Only use of RangeFilter

* FEATURE: Added TypedChoiceFilter

* FIXED: Correct logic for short circuit on MultipleChoiceFilter

    Added `always_filter` attribute and `is_noop()` test to apply short-circuiting.

    Set `always_filter` to `False` on init to apply default `is_noop()` test.
    Override `is_noop()` for more complex cases.

* MISC: Version bumping with ``bumpversion``


Version 0.8 (2014-09-29)
------------------------

 * FEATURE: Added exclusion filters support

 * FEATURE: Added `fields` dictionary shorthand syntax

 * FEATURE: Added `MethodFilter`.

 * FIXED: #115 "filters.Filter.filter() fails if it receives [] or () as value"

 * MISC: Various Documentation and Testing improvements



Version 0.7 (2013-08-10)
------------------------

 * FEATURE: Added support for AutoField.

 * FEATURE: There is a "distinct" flag to ensure that only unique rows are
   returned.

 * FEATURE: Support descending ordering (slighty backwards incompatible).

 * FEATURE: Support "strict" querysets, ie wrong filter data returns no results.

 * FIXED: Some translation strings were changed to be in line with admin.

 * FIXED: Support for Django 1.7.

Version 0.6 (2013-03-25)
------------------------

* raised minimum Django version to 1.4.x

* added Python 3.2 and Python 3.3 support

* added Django 1.5 support and initial 1.6 compatability

* FEATURE: recognition of custom model field subclasses

* FEATURE: allow optional display names for order_by values

* FEATURE: addition of class-based FilterView

* FEATURE: addition of count() method on FilterSet to prevent pagination
  from loading entire queryset

* FIXED: attempts to filter on reverse side of m2m, o2o or fk would
  raise an error


Version 0.5.4 (2012-11-16)
--------------------------

* project brought back to life
