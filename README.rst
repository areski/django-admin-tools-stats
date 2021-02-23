===================
Django admin charts
===================

:Description: Easily configurable charts statistics for ``django-admin`` and ``django-admin-tools``.
:Documentation: http://django-admin-charts.readthedocs.org/en/latest/

.. image:: https://travis-ci.org/PetrDlouhy/django-admin-charts.svg?branch=master
    :target: https://travis-ci.org/PetrDlouhy/django-admin-charts

.. image:: https://img.shields.io/pypi/v/django-admin-charts.svg
  :target: https://pypi.python.org/pypi/django-admin-charts/
  :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/django-admin-charts.svg
  :target: https://pypi.python.org/pypi/django-admin-charts/
  :alt: Downloads

.. image:: https://img.shields.io/pypi/pyversions/django-admin-charts.svg
  :target: https://pypi.python.org/pypi/django-admin-charts/
  :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/l/django-admin-charts.svg
  :target: https://pypi.python.org/pypi/django-admin-charts/
  :alt: License

.. inclusion-marker-do-not-remove

Create beautiful configurable charts from your models and display them on the ``django-admin`` index page or on ``django-admin-tools`` dashboard.
The charts are based on models and criterias defined through admin interface and some chart parameters are configurable in live view.

This is application is fork of `django-admin-tools-stats <https://github.com/areski/django-admin-tools-stats/>`_ which has been reworked to display all charts through Ajax and made work with plain ``django-admin``. The ``django-admin-tools`` are supported but not needed.

.. image:: https://github.com/PetrDlouhy/django-admin-charts/raw/master/docs/source/_static/stacked_area_chart.png
.. image:: https://github.com/PetrDlouhy/django-admin-charts/raw/master/docs/source/_static/bar_chart.png
.. image:: https://github.com/PetrDlouhy/django-admin-charts/raw/master/docs/source/_static/aoe_chart.png

============
Requirements
============

* ``Django>=2.0``
* ``Python>3.6``
* PostgreSQL (MySQL is experimental, other databases probably not working but PRs are welcome)
* ``simplejson`` for charts based on ``DecimalField`` values

============
Installation
============

Install django-admin-charts with these commands::

    $ pip install django-admin-charts



Basic setup for ``django-admin``
--------------------------------

Add ``admin_tools_stats`` (the Django admin charts application) & ``django_nvd3`` into INSTALLED_APPS in settings.py::

    INSTALLED_APPS = (
        'admin_tools_stats',  # this must be BEFORE 'admin_tools' and 'django.contrib.admin'
        'django_nvd3',
        ...
        'django.contrib.admin',
    )
    
Install the ``nvd3==1.7.1`` and ``d3==3.3.13`` javascript libraries. For installation with ``django-bower`` see section `Installation of javascript libraries with django-bower`_.
Set library paths if they differ from the ``django-bower`` defaults::

   ADMIN_CHARTS_NVD3_JS_PATH = 'bow/nvd3/build/nv.d3.js'
   ADMIN_CHARTS_NVD3_CSS_PATH = 'bow/nvd3/build/nv.d3.css'
   ADMIN_CHARTS_D3_JS_PATH = 'bow/d3/d3.js'

Register chart views in your ``urls.py``::

    from django.urls import include, path
    urlpatterns = [
        path('admin_tools_stats/', include('admin_tools_stats.urls')),
    ]

Run migrations::

    $ python manage.py migrate

Open admin panel, configure ``Dashboard Stats Criteria`` & ``Dashboard Stats`` respectively

======================
Special configurations
======================

Update from ``django-admin-tools-stats``
----------------------------------------

Uninstall ``django-admin-tools-stats``.

Follow ``django-admin-charts`` installation according to previous section. Especially pay attention to these steps:
- Move ``admin_tools_stats`` in ``INSTALLED_APPS`` before ``admin_tools`` and ``django.contrib.admin``.
- Configure ``urls.py``.

Change ``DashboardCharts`` to ``DashboardChart`` in dashboard definition (this is recomended even if dummy class is left for compatibility reasons).

Check any overridden template from ``admin_tools_stats`` or ``DashboardChart(s)`` class that might interfere with the changes.


Installation of javascript libraries with ``django-bower``
----------------------------------------------------------

Add ``django-bower`` to INSTALLED_APPS in settings.py::

    INSTALLED_APPS = (
        ...
        'djangobower'
    )

Add the following properties to you settings.py file::

    # Specifie path to components root (you need to use absolute path)
    BOWER_COMPONENTS_ROOT = os.path.join(PROJECT_ROOT, 'components')


    BOWER_INSTALLED_APPS = (
        'd3#3.3.13',
        'nvd3#1.7.1',
    )

Add django-bower finder to your static file finders::

    STATICFILES_FINDERS = (
        ...
        'djangobower.finders.BowerFinder',
    )

Run the following commands. These will download nvd3.js and its dependencies using bower and throw them in to you static folder for access by your application::

    $ python manage.py bower_install
    $ python manage.py collectstatic



Usage with ``django-admin-tools``
----------------------------------

Configure ``admin_tools``

Add following code to dashboard.py::

    from admin_tools_stats.modules import DashboardChart, get_active_graph

    # append an app list module
    self.children.append(modules.AppList(
        _('Dashboard Stats Settings'),
        models=('admin_tools_stats.*', ),
    ))

    # Copy following code into your custom dashboard
    # append following code after recent actions module or
    # a link list module for "quick links"
    graph_list = get_active_graph()
    for i in graph_list:
        kwargs = {}
        kwargs['require_chart_jscss'] = True
        kwargs['graph_key'] = i.graph_key

        for key in context['request'].POST:
            if key.startswith('select_box_'):
                kwargs[key] = context['request'].POST[key]

        self.children.append(DashboardChart(**kwargs))


You may also need to add some includes to your template admin base, see an example on the demo project::

    demoproject/demoproject/templates/admin/base_site.html


Usage on DB that doesn't support JSONFields
-------------------------------------------

You can add following line to your settings in order to use JSONField from `django-jsonfield` instead of native Django JSONField::

   ADMIN_CHARTS_USE_JSONFIELD = False

This can become handy, when deploying on MySQL<5.7 (Like AWS RDS Aurora)


============
Running demo
============

Run following commands::

   pip install -r requirements
   python manage.py migrate
   python manage.py loaddata demoproject/fixtures/auth_user.json
   python manage.py loaddata demoproject/fixtures/test_data.json
   python manage.py bower install
   python manage.py runserver

And log in with username `admin` and password `admin` to the `localhost:8000/admin` site.

===========
Development
===========

Dependencies
------------

django-admin-charts is a django based application, the major requirements are:

- django-jsonfield
- django-nvd3
- django-bower


Contributing
------------

If you've found a bug, add a feature or improve django-admin-charts and
think it is useful then please consider contributing.
Patches, pull requests or just suggestions are always welcome!

Source code: http://github.com/PetrDlouhy/django-admin-charts

Bug tracker: https://github.com/PetrDlouhy/django-admin-charts/issues


Debugging charts
----------------

For chart data view (/admin_tools_stats/chart_data/payments/) the URL query
parameter `&debug=True` can be added, in order to get Django debug page or
Django debug toolbar.


Documentation
-------------

Documentation is available on 'Read the Docs':
http://readthedocs.org/docs/django-admin-charts/


License
-------

django-admin-charts is licensed under MIT, see ``MIT-LICENSE.txt``.
