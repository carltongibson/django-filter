Version 1.1 (2017-10-19)
------------------------

* Add Deprecations for 2.0 (#792)
* Improve IsoDateTimeField test clarity (#790)
* Fix form attr references in tests (#789)
* Simplify tox config, drop python 3.3 & django 1.8 (#787)
* Make get_filter_name a classmethod, allowing it to be overriden for each FilterClass (#775)
* Support active timezone (#750)
* Docs Typo: django_filters -> filters in docs (#773)
* Add Polish translations for some messages (#771)
* Remove support for Django 1.9 (EOL) (#752)
* Use required attribute from field when getting schema fields (#766)
* Prevent circular ImportError hiding for rest_framework sub-package (#741)
* Deprecate 'extra' field attrs on Filter (#734)
* Add SuffixedMultiWidget (#681)
* Fix null filtering for *Choice filters (#680)
* Use isort on imports (#761)
* Use urlencode from django.utils.http (#760)
* Remove OrderingFilter.help_text (#757)
* Update DRF test dependency to 3.6 (#747)


Version 1.0.4 (2017-05-19)
--------------------------

Quick fix for verbose_field_name issue from 1.0.3 (#722)


Version 1.0.3 (2017-05-16)
--------------------------

Improves compatibility with Django REST Framework schema generation.

See the `1.0.3 Milestone`__ for full details.

__ https://github.com/carltongibson/django-filter/milestone/13?closed=1



Version 1.0.2 (2017-03-20)
--------------------------

Updates for compatibility with Django 1.11 and Django REST Framework 3.6.

Adds CI testing against Python 3.6

See the `1.0.2 Milestone`__ for full details.

__ https://github.com/carltongibson/django-filter/milestone/12?closed=1


Version 1.0.1 (2016-11-28)
--------------------------

Small release to ease compatibility with DRF:

* #568 Adds ``rest_framework`` to the ``django_filters`` namespace to allow single
  ``import django_filters` usage.
* A number of small updates to the docs


Version 1.0 (2016-11-17)
------------------------

This release removes all the deprecated code from 0.14 and 0.15 for 1.0 #480.

Please see the `Migration Notes`__ for details of how to migrate.
Stick with 0.15.3 if you're not ready to update.

__ https://github.com/carltongibson/django-filter/blob/1.0.0/docs/guide/migration.txt

The release includes a number of small fixes and documentation updates.

See the `1.0 Milestone`__ for full details.

__ https://github.com/carltongibson/django-filter/milestone/8?closed=1


Version 0.15.3 (2016-10-17)
---------------------------

Adds compatibility for DRF (3.5+) get_schema_fields filter backend
introspection.

* #492 Port get_schema_fields from DRF


Version 0.15.2 (2016-09-29)
---------------------------

* #507 Fix compatibility issue when not using the DTL


Version 0.15.1 (2016-09-28)
---------------------------

A couple of quick bug fixes:

* #496 OrderingFilter not working with Select widget

* #498 DRF Backend Templates not loading



Version 0.15.0 (2016-09-20)
---------------------------

This is a preparatory release for a 1.0. Lots of clean-up, lots of changes,
mostly backwards compatible.

Special thanks to Ryan P Kilby (@rpkilby) for lots of hard work.

Most changes should raise a Deprecation Warning.

**Note**: if you're doing *Clever Things™* with the various filter options
— ``filter_overrides`` etc — you may run into an `AttributeError` since these
are now defined on the metaclass and not on the filter itself.
(See the discussion on #459)

Summary: Highly Recommended, but take a moment to ensure everything still works.

* Added the DRF backend. #481

* Deprecated `MethodFilter` in favour of `Filter.method` #382

* Move filter options to metaclass #459

* Added `get_filter_predicate` hook. (Allows e.g. filtering on annotated fields) #469

* Rework Ordering options into a filter #472

* Hardened all deprecations for 1.0. Please do see the `Migration Notes`__

__ https://github.com/carltongibson/django-filter/blob/1.0.0/docs/guide/migration.txt



Version 0.14.0 (2016-08-14)
---------------------------

* Confirmed support for Django 1.10.

* Add support for filtering on DurationField (new in Django 1.8).

* Fix UUIDFilter import issue

* Improve FieldLookupError message

* Add filters_for_model to improve extensibility

* Fix limit_choices_to behavior with callables

* Fix distinct behavior for range filters

* Various Minor Clean up issues.


Version 0.13.0 (2016-03-11)
---------------------------

* Add support for filtering by CSV #363

* Add DateTimeFromToRangeFilter #376

* Add Chinese translation #359

* Lots of fixes.


Version 0.12.0 (2016-01-07)
---------------------------

* Raised minimum Django version to 1.8.x

* FEATURE: Add support for custom ORM lookup types #221

* FEATURE: Add JavaScript friendly BooleanWidget #270

* FIXED: (More) Compatability with Django 1.8 and Django 1.9+

* BREAKING CHANGE: custom filter names are now also be used for ordering #230

    If you use ordering on a field you defined as custom filter with custom
    name, you should now use the filter name as ordering key as well.

    Eg. For a filter like :

        class F(FilterSet):
            account = CharFilter(name='username')
            class Meta:
                model = User
                fields = ['account', 'status']
                order_by = True

     Before, ordering was like `?o=username`. Since 0.12.0 it's `o=account`.


Version 0.11.0 (2015-08-14)
---------------------------

* FEATURE: Added default filter method lookup for MethodFilter #222

* FEATURE: Added support for yesterday in daterangefilter #234

* FEATURE: Created Filter for NumericRange. #236

* FEATURE: Added Date/time range filters #215

* FEATURE: Added option to raise with `strict` #255

* FEATURE: Added Form Field and Filter to parse ISO-8601 timestamps


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
