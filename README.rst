Django-admin-tools-stats
------------------------

:Description: Django-admin module to create charts and stats in your dashboard
:Documentation: http://django-admin-tools-stats.readthedocs.org/en/latest/


Django-admin-tools-stats is a Django admin module that allow you to create easily charts on your dashboard based on specific models and criterias.

It will query your models and provide reporting and statistics graphs, simple to read and display on your Dashboard.

.. image:: https://github.com/Star2Billing/django-admin-tools-stats/raw/master/docs/source/_static/admin_dashboard.png


Installation
------------

Install, upgrade and uninstall django-admin-tools-stats with these commands::

    $ pip install django-admin-tools-stats


Dependencies
------------

django-admin-tools-stats is a django based application, the major requirements are :

    - python-dateutil>=1.5,<2.0
    - django-jsonfield==0.8
    - django-qsstats-magic>=0.6.1
    - python-memcached>=1.47
    - django-cache-utils
    - django-admin-tools>=0.5.0
    - switch2bill-common>=2.6.0
    - django-nvd3>=0.4.1


Configure
---------

- Configure ``admin_tools``
- Add ``admin_tools_stats`` & ``django_nvd3`` into INSTALLED_APPS in settings.py::

    INSTALLED_APPS = (
        ...
        'admin_tools_stats',
        'django_nvd3',
    )

- Add following code to dashboard.py::

    from admin_tools_stats.modules import DashboardCharts, get_active_graph

    # append an app list module for "Country_prefix"
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
        kwargs['require_chart_jscss'] = False
        kwargs['graph_key'] = i.graph_key

        if request.POST.get('select_box_' + i.graph_key):
            kwargs['select_box_' + i.graph_key] = request.POST['select_box_' + i.graph_key]

        self.children.append(DashboardCharts(**kwargs))

- To create the tables needed by Django-admin-tools-stats, run the following command::

    $ python manage.py syncdb


- Open admin panel, configure ``Dashboard Stats Criteria`` & ``Dashboard Stats respectively``


Contributing
------------

If you've found a bug, add a feature or improve django-admin-tools-stats and
think it is useful then please consider contributing.
Patches, pull requests or just suggestions are always welcome!

Source code: http://github.com/Star2Billing/django-admin-tools-stats

Bug tracker: https://github.com/Star2Billing/django-admin-tools-stats/issues


Documentation
-------------

Documentation is available on 'Read the Docs':
http://readthedocs.org/docs/django-admin-tools-stats/


License
-------

Copyright (c) 2011-2014 Star2Billing S.L. <info@star2billing.com>

django-admin-tools-stats is licensed under MIT, see `MIT-LICENSE.txt`.
