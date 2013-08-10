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
