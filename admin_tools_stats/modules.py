# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from qsstats import QuerySetStats
from cache_utils.decorators import cached
from admin_tools.dashboard import modules
from admin_tools_stats.models import DashboardStats
from datetime import datetime, timedelta
import time

# Make timezone aware for Django 1.4
try:
    from django.utils.timezone import now
except ImportError:
    now = datetime.now


class DashboardChart(modules.DashboardModule):
    """Dashboard module with user registration charts.

    Default values are best suited for 2-column dashboard layouts.
    """
    title = _('Dashboard Stats')
    template = 'admin_tools_stats/modules/chart.html'
    days = None
    interval = 'days'
    tooltip_date_format = "%d %b %Y"
    x_axis_format = "%d %b %Y"
    chart_type = 'discreteBarChart'
    chart_height = 300
    chart_width = '100%'
    require_chart_jscss = False

    model = None
    graph_key = None
    filter_list = None

    def is_empty(self):
        return False

    def __init__(self, *args, **kwargs):
        super(DashboardChart, self).__init__(*args, **kwargs)
        self.select_box_value = ''
        for key in kwargs:
            self.require_chart_jscss = kwargs['require_chart_jscss']
            self.graph_key = kwargs['graph_key']
            if kwargs.get('select_box_' + self.graph_key):
                self.select_box_value = kwargs['select_box_' + self.graph_key]

        if self.days is None:
            #self.days = {'days': 30, 'weeks': 30*7, 'months': 30*12}[self.interval]
            self.days = {'hours': 24, 'days': 7, 'weeks': 7 * 1, 'months': 30 * 2}[self.interval]

        self.data = self.get_registrations(self.interval, self.days,
                                           self.graph_key, self.select_box_value)
        self.prepare_template_data(
            self.data, self.graph_key, self.select_box_value)

    def get_caption(self, dt):
        """Displays caption on the x-axis of dashboard graph"""
        return {
            'hours': dt.strftime("%H"),
            'days': dt.strftime("%a"),
            'months': dt.strftime("%b"),
            'weeks': dt.strftime('%W'),
        }[self.interval]

    #@cached(60 * 5)
    def get_registrations(self, interval, days, graph_key, select_box_value):
        """ Returns an array with new users count per interval."""
        try:
            conf_data = DashboardStats.objects.get(graph_key=graph_key)
            model_name = get_model(
                conf_data.model_app_name, conf_data.model_name)
            kwargs = {}

            for i in conf_data.criteria.all():
                # fixed mapping value passed info kwargs
                if i.criteria_fix_mapping:
                    for key in i.criteria_fix_mapping:
                        # value => i.criteria_fix_mapping[key]
                        kwargs[key] = i.criteria_fix_mapping[key]

                # dynamic mapping value passed info kwargs
                if i.dynamic_criteria_field_name and select_box_value:
                    kwargs[i.dynamic_criteria_field_name] = select_box_value

            stats = QuerySetStats(model_name.objects.filter(**kwargs),
                                  conf_data.date_field_name)
            #stats = QuerySetStats(User.objects.filter(is_active=True), 'date_joined')
            today = now()
            if days == 24:
                begin = today - timedelta(hours=days - 1)
                return stats.time_series(begin, today + timedelta(hours=1), interval)

            begin = today - timedelta(days=days - 1)
            return stats.time_series(begin, today + timedelta(days=1), interval)
        except:
            User = get_user_model()
            stats = QuerySetStats(
                User.objects.filter(is_active=True), 'date_joined')
            today = now()
            if days == 24:
                begin = today - timedelta(hours=days - 1)
                return stats.time_series(begin, today + timedelta(hours=1), interval)
            begin = today - timedelta(days=days - 1)
            return stats.time_series(begin, today + timedelta(days=1), interval)

    def prepare_template_data(self, data, graph_key, select_box_value):
        """ Prepares data for template (passed as module attributes) """
        self.captions = [self.get_caption(t[0]) for t in data]

        if self.interval == 'months':
            self.tooltip_date_format = self.x_axis_format = "%b"
        elif self.interval == 'days':
            self.tooltip_date_format = "%d %b %Y"
            self.x_axis_format = "%a"
        elif self.interval == 'hours':
            self.tooltip_date_format = "%d %b %Y %H:%S"
            self.x_axis_format = "%H"

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

        self.max_value = max(self.values)
        self.form_field = get_dynamic_criteria(graph_key, select_box_value)


def get_title(graph_key):
    """Returns graph title"""
    try:
        conf_data = DashboardStats.objects.get(graph_key=graph_key)
        return conf_data.graph_title
    except:
        return ''


def get_dynamic_criteria(graph_key, select_box_value):
    """To get dynamic criteria & return into select box to display on dashboard"""
    try:
        temp = ''
        conf_data = DashboardStats.objects.get(graph_key=graph_key)
        for i in conf_data.criteria.all():
            dy_map = i.criteria_dynamic_mapping
            if dy_map:
                temp = '<select name="select_box_' + graph_key + '" onChange="$(\'#stateform\').submit();">'
                for key in dict(dy_map):
                    value = dy_map[key]
                    if key == select_box_value:
                        temp += '<option value="' + \
                            key + '" selected=selected>' + value + '</option>'
                    else:
                        temp += '<option value="' + \
                            key + '">' + value + '</option>'
                temp += '</select>'

        return mark_safe(force_unicode(temp))
    except:
        return ''


def get_active_graph():
    """Returns active graphs"""
    graph_list = []
    try:
        graph_list = DashboardStats.objects.filter(is_visible=1)
        return graph_list
    except:
        return graph_list


def get_registration_charts(**kwargs):
    """ Returns 3 basic chart modules (today, last 7 days & last 3 months) """
    return [
        DashboardChart(_('today').title(), interval='hours', **kwargs),
        DashboardChart(_('last week').title(), interval='days', **kwargs),
        #DashboardChart(_('Last 2 Weeks'), interval='weeks', **kwargs),
        DashboardChart(_('last months').title(), interval='months', **kwargs),
    ]


class DashboardCharts(modules.Group):
    """Group module with 3 default dashboard charts"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('children', get_registration_charts(**kwargs))
        super(DashboardCharts, self).__init__(*args, **kwargs)
