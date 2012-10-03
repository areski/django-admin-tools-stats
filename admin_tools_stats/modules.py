# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db.models import get_model
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from qsstats import QuerySetStats
from cache_utils.decorators import cached
from admin_tools.dashboard import modules
from admin_tools_stats.models import DashboardStats
from datetime import datetime, timedelta


class DashboardChart(modules.DashboardModule):
    """Dashboard module with user registration charts.

    Default values are best suited for 2-column dashboard layouts.
    """
    title = _('Dashboard Stats')
    template = 'admin_tools_stats/modules/chart.html'
    chart_size = "380x100"
    days = None
    interval = 'days'

    model = None
    graph_key = None
    filter_list = None

    def is_empty(self):
        return False

    def __init__(self, *args, **kwargs):
        super(DashboardChart, self).__init__(*args, **kwargs)
        self.select_box_value = ''
        for key in kwargs:
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

    @cached(60 * 5)
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
            today = datetime.today()
            if days == 24:
                begin = today - timedelta(hours=days - 1)
                return stats.time_series(begin, today + timedelta(hours=1), interval)

            begin = today - timedelta(days=days - 1)
            return stats.time_series(begin, today + timedelta(days=1), interval)
        except:
            stats = QuerySetStats(
                User.objects.filter(is_active=True), 'date_joined')
            today = datetime.today()
            if days == 24:
                begin = today - timedelta(hours=days - 1)
                return stats.time_series(begin, today + timedelta(hours=1), interval)
            begin = today - timedelta(days=days - 1)
            return stats.time_series(begin, today + timedelta(days=1), interval)

    def prepare_template_data(self, data, graph_key, select_box_value):
        """ Prepares data for template (passed as module attributes) """
        self.captions = [self.get_caption(t[0]) for t in data]
        self.values = [t[1] for t in data]
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
                temp = '<select name="select_box_' + graph_key + '" onChange="this.form.submit();">'
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
    for key in kwargs:
        #value = kwargs[key]
        key_value = kwargs['graph_key']
    return [
        DashboardChart(_('Today'), interval='hours', **kwargs),
        DashboardChart(_('Last week'), interval='days', **kwargs),
        #DashboardChart(_('Last 2 Weeks'), interval='weeks', **kwargs),
        DashboardChart(_('Last months'), interval='months', **kwargs),
    ]


class DashboardCharts(modules.Group):
    """Group module with 3 default dashboard charts"""
    #title = _('New Users')
    key_value = ''

    def __init__(self, *args, **kwargs):
        for key in kwargs:
            #value = kwargs[key]
            key_value = kwargs['graph_key']
        kwargs.setdefault('children', get_registration_charts(**kwargs))
        super(DashboardCharts, self).__init__(*args, **kwargs)
        self.title = get_title(key_value)
