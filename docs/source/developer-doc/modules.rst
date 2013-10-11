.. _modules:

Django-admin-tools-stats Modules
================================

.. _DashboardChart:

:class:`DashboardChart`
-----------------------

Dashboard module with user registration charts. Default values are best suited
for 2-column dashboard layouts.

    def **get_registrations(self, interval, days, graph_key, select_box_value):**
        Returns an array with new users count per interval.

    def **prepare_template_data(self, data, graph_key, select_box_value):**
        Prepares data for template (passed as module attributes)


.. _DashboardCharts:

:class:`DashboardCharts`
------------------------

Group module with 3 default dashboard charts
