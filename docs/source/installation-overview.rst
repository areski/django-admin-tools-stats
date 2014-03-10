.. _installation-overview:

=====================
Installation overview
=====================

.. _install-requirements:

Install requirements
====================

To get started with Django-admin-tools-stats you must have the following installed:

- Django Framework >= 1.4 (Python based Web framework)
- python-dateutil >= 1.5 (Extensions to the standard datetime module)
- django-admin-tools (Collection of tools for Django administration)
- django-cache-utils (To provide utilities for making cache-related work easier)
- django-jsonfield >= 0.6 (Reusable Django field that can use inside models)
- django-nvd3 >= 0.5.0 (Django wrapper for nvd3 - It's time for beautiful charts)
- python-memcached >= 1.47 (Python based API for communicating with the memcached
distributed memory object cache daemon)


Use PIP to install the dependencies listed in the requirments file,::

    $ pip install -r requirements.txt


.. _configuration:

Configuration
=============

- Configure django-admin-tools, refer to the documentation of http://django-admin-tools.readthedocs.org/en/latest/

- Add ``admin_tools_stats`` & ``django_nvd3`` into INSTALLED_APPS in settings.py::

    INSTALLED_APPS = (
        'admin_tools_stats',
        'django_nvd3',
    )

- Add the following code to your file dashboard.py::

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
        kwargs['graph_key'] = i.graph_key
        kwargs['require_chart_jscss'] = False

        if context['request'].POST.get('select_box_' + i.graph_key):
            kwargs['select_box_' + i.graph_key] = context['request'].POST['select_box_' + i.graph_key]

        self.children.append(DashboardCharts(**kwargs))

- To create the tables needed by Django-admin-tools-stats, run the following command::

    $ python manage.py syncdb


- Open admin panel, configure ``Dashboard Stats Criteria`` & ``Dashboard Stats`` respectively
