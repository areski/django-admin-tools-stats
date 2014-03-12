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

    - python-dateutil
    - django-jsonfield
    - django-qsstats-magic
    - django-cache-utils
    - django-admin-tools
    - django-nvd3
    - django-bower


Configure
---------

- Configure ``admin_tools``
- Configure ``django-bower``

  - Add ``django-bower`` to INSTALLED_APPS in settings.py::

        INSTALLED_APPS = (
            ...
            'djangobower'
        )
    
  - Add the following properties to you settings.py file::

        BOWER_COMPONENTS_ROOT = BASE_DIR

        BOWER_INSTALLED_APPS = ('nvd3',)

  - Add django-bower finder to your static file finders::

        STATICFILES_FINDERS = (
            ...
            'djangobower.finders.BowerFinder',
        )

  - Run the following commands. These will download nvd3.js and its dependencies using bower and throw them in to you static folder for access by your application::

        $ python manage.py bower_install 
        $ python manage.py collectstatic

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
        kwargs['require_chart_jscss'] = True
        kwargs['graph_key'] = i.graph_key

        if context['request'].POST.get('select_box_' + i.graph_key):
            kwargs['select_box_' + i.graph_key] = context['request'].POST['select_box_' + i.graph_key]

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
