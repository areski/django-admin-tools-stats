
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
import warnings

from admin_tools.dashboard import modules

from django.contrib import messages

from .models import DashboardStats


class DashboardChart(modules.DashboardModule):
    """Dashboard module with user registration charts.

    Default values are best suited for 2-column dashboard layouts.
    """
    template = 'admin_tools_stats/modules/chart.html'
    days = None
    require_chart_jscss = False
    extra = {}
    chart_height = 300
    chart_width = '100%'

    model = None
    graph_key = None
    filter_list = None
    chart_container = None

    def is_empty(self):
        return False

    def __init__(self, *args, **kwargs):
        super(DashboardChart, self).__init__(*args, **kwargs)
        self.require_chart_jscss = kwargs['require_chart_jscss']
        global stat_dict  # We use this to came around current implementations of Dashboards which are query inefective
        self.dashboard_stats = stat_dict[self.graph_key]
        self.title = self.get_title(self.graph_key)

    def init_with_context(self, context):
        super(DashboardChart, self).init_with_context(context)
        request = context['request']

        self.prepare_module_data(self.graph_key)

        self.form_field = self.get_control_form(self.graph_key)

        if hasattr(self, 'error_message'):
            messages.add_message(request, messages.ERROR, "%s dashboard: %s" % (self.title, self.error_message))

    def prepare_module_data(self, graph_key):
        """ Prepares data for template (passed as module attributes) """
        self.chart_container = "chart_container_" + self.graph_key
        self.id = 'chart_' + self.graph_key

    def get_title(self, graph_key):
        """Returns graph title"""
        try:
            return self.dashboard_stats.graph_title
        except LookupError as e:
            self.error_message = str(e)
            return ''

    def get_control_form(self, graph_key):
        """To get dynamic criteria & return into select box to display on dashboard"""
        try:
            return self.dashboard_stats.get_control_form()
        except LookupError as e:
            self.error_message = str(e)
            return ''


def get_active_graph():
    """Returns active graphs"""
    global stat_dict
    stat_dict = {}
    stats = DashboardStats.get_active_graph()
    for stat in stats:
        stat_dict[stat.graph_key] = stat
    return stats


class DashboardCharts(DashboardChart):
    """Deprecated class left for compatibility."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "DashboardCharts are not required anymore. Use just DashboardChart instead",
            PendingDeprecationWarning
        )
        super(DashboardCharts, self).__init__(*args, **kwargs)
