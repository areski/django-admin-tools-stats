.. _installation-overview:

=====================
Installation overview
=====================

.. _install-requirements:

Install requirements
====================

A Requirements file gives you a way to create an environment where you can put
all optional dependencies which are needed for your Project/Application.

To get started with Django-admin-tools-stats you must have the following installed:

- python >= 2.4 (programming language)
- Apache / http server with WSGI modules
- Django Framework >= 1.3 (Python based Web framework)
- MySQL-python >= 1.2.3 (MySQL for python language)
- python-dateutil >= 1.5 (Extensions to the standard datetime module)
- django-admin-tools (Collection of tools for the django administration)
- django-chart-tools >= 0.2.1 (A thin wrapper around Google Chart API for charts)
- django-cache-utils (To provide utils for making cache-related work easier)
- django-jsonfield >= 0.6 (Reusable django field that can use inside models)
- python-memcached >= 1.47 (Python based API for communicating with the memcached distributed memory object cache daemon)


Use PIP to install all the requirements,::

    $ pip install -r requirements.txt


.. _configuration:

Configuration
=============

- Configure ``admin_tools``
- Add ``admin_tools_stats`` & ``chart_tools`` into INSTALLED_APPS in settings.py::

    INSTALLED_APPS = (
        ...
        'admin_tools_stats',
        'chart_tools',
        ...)

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
        kwargs['graph_key'] = i.graph_key
        if request.POST.get('select_box_'+i.graph_key):
            kwargs['select_box_'+i.graph_key] = request.POST['select_box_'+i.graph_key]

        self.children.append(DashboardCharts(**kwargs))

- Do ``manage.py syncdb``
- Open admin panel, Configure ``Dashboard Stats Criteria`` & ``Dashboard Stats respectively``
