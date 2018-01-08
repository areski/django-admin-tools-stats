Changelog
=========


0.9.0 (2018-01-08)
------------------

* Count added <Petr Dlouhý>
* fix Travist configuration and Django versions in it <Petr Dlouhý>
* other fixes for Django 2.0 <Petr Dlouhý>
* use djcacheutils for Python 3 compatibility <Petr Dlouhý>

0.8.0 (2017-01-18)
------------------

* make possible to change dateformat of x axis <Petr Dlouhý>
* add example for dynamic criteria <Petr Dlouhý>
* test also dynamic criteria <Petr Dlouhý>
* use django-qsstats-magic that work with Python 3 in tests <Petr Dlouhý>
* test actual chart generation -> increase test coverage <Petr Dlouhý>
* fix: preserve criteria settings of other chart stats <Petr Dlouhý>
* fix duplicate id of dynamic criteria form <Petr Dlouhý>
* reduce size of generated code by reusing load_charts code in function <Petr Dlouhý>
* fix duplication of % sign in template svg tag <Petr Dlouhý>
* catch also TypeError in registration field <Petr Dlouhý>
* rename "Graph key" to "Graph identifier" to be more clear <Petr Dlouhý>
* use save_as=True in admin to allow easier copying of charts <Petr Dlouhý>
* allow to override day intervalse for graphs <Petr Dlouhý>
* reorganize testing to run coverage <Petr Dlouhý>
* remove old import code <Petr Dlouhý>
* checks of DashboardStats field values, report field errors by Django message framework <Petr Dlouhý>



0.7.1 (2016-08-17)
------------------

* fix travis-ci tests Django & Python version


0.7.0 (2016-08-17)
-------------------

* fixes for newer Django and Python versions
* add Travis configuration file
* allow to override get_registration_charts function
* fix Python 3 compatibility
* python manage.py bower_install creates the folder build for src


0.6.6 (2015-12-13)
-------------------

* remove null=True on ManyToManyField


0.6.5 (2015-12-13)
-------------------

* add migrations


0.6.4 (2015-12-12)
-------------------

* fix bower_install creates a the folder build for src


0.6.3 (2015-12-11)
-------------------

* support for django 1.9 - depreciated get_model


0.6.2 (2015-12-10)
-------------------

* remove python-memcached from requirements


0.6.1 (2014-05-30)
-------------------

* support of Aggregation functions


0.5.5 (2014-02-06)
-------------------

* fix setup with requirement.txt file


0.5.4 (2014-02-06)
-------------------

* get rid of dependencies


0.5.3 (2014-01-03)
-------------------

* Fix js async loading with recent jquery version


0.5.2 (2014-01-01)
-------------------

* Fix requirements to not force old version of jsonfield


0.5.1 (2013-10-11)
-------------------

* Fix some bug on the tabs behavior and tooltip of the charts
* Update documentation


0.5.0 (2013-10-09)
-------------------

* Support for Django-NVD3


0.4.3 (2013-03-26)
------------------

* fix requirements - dep to django-admin-tools>=0.5.0


0.4.2 (2013-03-07)
------------------

* Update trans string


0.4.1 (2012-12-19)
------------------

* Fix requirement for switch2bill-common


0.4 (2012-11-19)
------------------

* Fix for Django 1.4 timezone support by vdboor (Diederik van der Boor)


0.3 (2012-10-03)
------------------

* Improve setup.py and update manifest
* Update README.rst
* Fix PEP8


0.2 (2011-05-22)
----------------

* Import project
