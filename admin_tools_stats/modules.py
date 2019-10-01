
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

from django.db.models.aggregates import Count, Sum, Avg, Max, Min, StdDev, Variance
from django.contrib.auth import get_user_model
from django.apps import apps
try:  # Python 3
    from django.utils.encoding import force_text
except ImportError:  # Python 2
    from django.utils.encoding import force_unicode as force_text
from django.contrib import messages
from django.core.exceptions import FieldError
from django.utils.safestring import mark_safe
from qsstats import QuerySetStats
from cache_utils.decorators import cached
from admin_tools.dashboard import modules
from admin_tools_stats.models import DashboardStats
from datetime import datetime, timedelta

import time

from django.utils.timezone import now


class DashboardChart(modules.DashboardModule):
    """Dashboard module with user registration charts.

    Default values are best suited for 2-column dashboard layouts.
    """
    template = 'admin_tools_stats/modules/chart.html'
    days = None
    interval = 'days'
    tooltip_date_format = "%d %b %Y"
    interval_dateformat_map = {
        'months': ("%b %Y", "%b"),
        'days': ("%d %b %Y", "%a"),
        'hours': ("%d %b %Y %H:%S", "%H"),
    }
    chart_type = 'discreteBarChart'
    chart_height = 300
    chart_width = '100%'
    require_chart_jscss = False
    extra = dict()

    model = None
    graph_key = None
    filter_list = None
    chart_container = None

    def is_empty(self):
        return False

    def __init__(self, *args, **kwargs):
        super(DashboardChart, self).__init__(*args, **kwargs)
        self.select_box_value = ''
        self.other_select_box_values = {}
        self.require_chart_jscss = kwargs['require_chart_jscss']
        self.time_since = kwargs.get('time_since', None)
        self.time_until = kwargs.get('time_until', None)
        self.graph_key = kwargs['graph_key']
        self.title = get_title(self.graph_key)
        for key in kwargs:
            if key.startswith('select_box_'):
                if key == 'select_box_' + self.graph_key:
                    self.select_box_value = kwargs[key]
                else:
                    self.other_select_box_values[key] = kwargs[key]

    def init_with_context(self, context):
        super(DashboardChart, self).init_with_context(context)
        request = context['request']

        self.data = []
        self.prepare_template_data(self.data, self.graph_key, self.select_box_value, self.other_select_box_values)

        if hasattr(self, 'error_message'):
            messages.add_message(request, messages.ERROR, "%s dashboard: %s" % (self.title, self.error_message))

    def init_with_context_ajax(self, context):
        super(DashboardChart, self).init_with_context(context)
        request = context['request']

        self.data = self.get_registrations(request.user, self.interval,
                                           self.graph_key, request.GET)
        self.prepare_template_data(self.data, self.graph_key, self.select_box_value, self.other_select_box_values)

        if hasattr(self, 'error_message'):
            messages.add_message(request, messages.ERROR, "%s dashboard: %s" % (self.title, self.error_message))

    @cached(60 * 5)
    def get_registrations(self, user, interval, graph_key, get_params):
        """ Returns an array with new users count per interval."""
        try:
            conf_data = DashboardStats.objects.get(graph_key=graph_key)
            model_name = apps.get_model(conf_data.model_app_name, conf_data.model_name)
            kwargs = {}
            if not user.is_superuser and conf_data.user_field_name:
                kwargs[conf_data.user_field_name] = user
            for i in conf_data.criteria.all():
                # fixed mapping value passed info kwargs
                if i.criteria_fix_mapping:
                    for key in i.criteria_fix_mapping:
                        # value => i.criteria_fix_mapping[key]
                        kwargs[key] = i.criteria_fix_mapping[key]

                # dynamic mapping value passed info kwargs
                dynamic_key = "select_box_dynamic_%i" % i.id
                if dynamic_key in get_params:
                    if get_params[dynamic_key] != '':
                        kwargs[i.dynamic_criteria_field_name] = get_params[dynamic_key]

            aggregate = None
            if conf_data.type_operation_field_name and conf_data.operation_field_name:
                operation = {
                    'DistinctCount': Count(conf_data.operation_field_name, distinct=True),
                    'Count': Count(conf_data.operation_field_name),
                    'Sum': Sum(conf_data.operation_field_name),
                    'Avg': Avg(conf_data.operation_field_name),
                    'StdDev': StdDev(conf_data.operation_field_name),
                    'Max': Max(conf_data.operation_field_name),
                    'Min': Min(conf_data.operation_field_name),
                    'Variance': Variance(conf_data.operation_field_name),
                }
                aggregate = operation[conf_data.type_operation_field_name]

            stats = QuerySetStats(model_name.objects.filter(**kwargs).distinct(),
                                  conf_data.date_field_name, aggregate)
            # stats = QuerySetStats(User.objects.filter(is_active=True), 'date_joined')
            return stats.time_series(self.time_since, self.time_until, interval)
        except (LookupError, FieldError, TypeError) as e:
            self.error_message = str(e)
            User = get_user_model()
            stats = QuerySetStats(
                User.objects.filter(is_active=True), 'date_joined')
            return stats.time_series(self.time_since, self.time_until, interval)

    @cached(60 * 5)
    def prepare_template_data(self, data, graph_key, select_box_value, other_select_box_values):
        """ Prepares data for template (passed as module attributes) """
        self.extra = {
            'x_is_date': True,
            'tag_script_js': False,
            'jquery_on_ready': False,
        }

        if self.interval in self.interval_dateformat_map:
            self.tooltip_date_format, self.extra['x_axis_format'] = self.interval_dateformat_map[self.interval]

        self.chart_container = "chart_container_" + self.graph_key
        # add string into href attr
        self.id = self.interval + '_' + self.graph_key

        xdata = []
        ydata = []
        for data_date in self.data:
            start_time = int(time.mktime(data_date[0].timetuple()) * 1000)
            xdata.append(start_time)
            ydata.append(data_date[1])

        extra_serie = {"tooltip": {"y_start": "", "y_end": ""},
                       "date_format": self.tooltip_date_format}

        self.values = {
            'x': xdata,
            'name1': self.interval, 'y1': ydata, 'extra1': extra_serie,
        }

        self.form_field = get_dynamic_criteria(graph_key, select_box_value, other_select_box_values)


@cached(60 * 5)
def get_title(graph_key):
    """Returns graph title"""
    try:
        return DashboardStats.objects.get(graph_key=graph_key).graph_title
    except LookupError as e:
        self.error_message = str(e)
        return ''


@cached(60 * 5)
def get_dynamic_criteria(graph_key, select_box_value, other_select_box_values):
    """To get dynamic criteria & return into select box to display on dashboard"""
    try:
        temp = ''
        conf_data = DashboardStats.objects.get(graph_key=graph_key).criteria.all()
        for i in conf_data:
            dy_map = i.criteria_dynamic_mapping
            if dy_map:
                temp += i.criteria_name + ': <select class="chart-input dynamic_criteria_select_box" name="select_box_dynamic_%i" >' % i.id
                for key in dict(dy_map):
                    value = dy_map[key]
                    if key == select_box_value:
                        temp += '<option value="' + key + '" selected=selected>' + value + '</option>'
                    else:
                        temp += '<option value="' + key + '">' + value + '</option>'
                temp += '</select>'

        temp += "\n".join(['<input type="hidden" name="%s" value="%s">' % (key, other_select_box_values[key]) for key in other_select_box_values ])

        temp += '<input type="hidden" class="hidden_graph_key" name="graph_key" value="%s">' % graph_key
        temp += 'Aggregation: <select class="chart-input select_box_interval" name="select_box_interval" >'
        for interval in ('hours', 'days', 'weeks', 'months', 'years'):
            selected_str = 'selected=selected' if interval == 'days' else ''
            temp += '<option class="chart-input" value="' + interval + '" ' + selected_str + '>' + interval + '</option>'
        temp += '</select>'
        temp += 'Date since: <input class="chart-input select_box_date_since" type="date" name="time_since" value="%s">' % (now() - timedelta(days=21)).strftime('%Y-%m-%d')
        temp += 'Date until: <input class="chart-input select_box_date_since" type="date" name="time_until" value="%s">' % now().strftime('%Y-%m-%d')

        return mark_safe(force_text(temp))
    except LookupError as e:
        self.error_message = str(e)
        return ''


def get_active_graph():
    """Returns active graphs"""
    try:
        return DashboardStats.objects.filter(is_visible=1)
    except LookupError as e:
        self.error_message = str(e)
        return []


class DashboardCharts(DashboardChart):
    """Deprecated class left for compatibility."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "DashboardCharts are not required anymore. Use just DashboardChart instead",
             PendingDeprecationWarning
        )
        super(DashboardCharts, self).__init__(*args, **kwargs)
