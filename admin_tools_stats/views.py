import logging
import time
from collections import OrderedDict
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from .models import DashboardStats

logger = logging.getLogger(__name__)


class AdminChartsView(TemplateView):
    template_name = 'admin_tools_stats/admin_charts.js'


interval_dateformat_map_bar_chart = {
    'years': ("%Y", "%Y"),
    'quarters': ("%b %Y", "%b"),
    'months': ("%b %Y", "%b"),
    'weeks': ("%a %d %b %Y", "%W"),
    'days': ("%a %d %b %Y", "%a"),
    'hours': ("%a %d %b %Y %H:%S", "%H"),
}

interval_dateformat_map = {
    'years': ("%Y", "%Y"),
    'quarters': ("%b %Y", "%b %Y"),
    'months': ("%b %Y", "%b %Y"),
    'weeks': ("%W (%d %b %Y)", "%W"),
    'days': ("%a %d %b %Y", "%d %b %Y"),
    'hours': ("%a %d %b %Y %H:%S", "%H"),
}


def get_dateformat(interval, chart_type):
    if chart_type == "discreteBarChart":
        return interval_dateformat_map_bar_chart[interval]
    return interval_dateformat_map[interval]


class ChartDataView(TemplateView):
    template_name = 'admin_tools_stats/chart_data.html'

    def get_context_data(self, *args, interval=None, graph_key=None, **kwargs):
        dashboard_stats = DashboardStats.objects.get(graph_key=graph_key)
        context = super().get_context_data(*args, **kwargs)

        if not(self.request.user.has_perm('admin_tools_stats.view_dashboardstats') or dashboard_stats.show_to_users):
            context['error'] = "You have no permission to view this chart. Check if you are logged in"
            context['graph_title'] = dashboard_stats.graph_title
            return context

        interval = self.request.GET.get('select_box_interval', interval) or dashboard_stats.default_time_scale
        operation = self.request.GET.get('select_box_operation') or dashboard_stats.type_operation_field_name
        operation_field = self.request.GET.get('select_box_operation_field') or dashboard_stats.operation_field_name
        context['chart_type'] = self.request.GET.get('select_box_chart_type') or dashboard_stats.default_chart_type
        try:
            time_since = datetime.strptime(self.request.GET.get('time_since', None), '%Y-%m-%d')
            time_until = datetime.strptime(self.request.GET.get('time_until', None), '%Y-%m-%d')
        except ValueError:
            return context

        try:
            series = dashboard_stats.get_multi_time_series(
                self.request.GET, time_since, time_until, interval, operation, operation_field, self.request.user,
            )
        except Exception as e:
            if 'debug' in self.request.GET:
                raise e
            context['error'] = str(e)
            context['graph_title'] = dashboard_stats.graph_title
            logger.exception(e)
            return context
        criteria = dashboard_stats.get_multi_series_criteria(self.request.GET)
        if criteria:
            current_tz = timezone.get_current_timezone()
            time_since_tz = time_since.astimezone(current_tz)
            time_until_tz = time_until.astimezone(current_tz).replace(hour=23, minute=59)
            choices = criteria.get_dynamic_choices(time_since_tz, time_until_tz)
        else:
            choices = {}

        ydata_serie = {}
        names = {}
        xdata = []
        serie_i_map = OrderedDict()
        for date in sorted(series.keys(), key=lambda d: datetime(d.year, d.month, d.day, getattr(d, 'hour', 0))):
            xdata.append(int(time.mktime(date.timetuple()) * 1000))
            for key, value in series[date].items():
                if key not in serie_i_map:
                    serie_i_map[key] = len(serie_i_map)
                y_key = 'y%i' % serie_i_map[key]
                if y_key not in ydata_serie:
                    ydata_serie[y_key] = []
                    names['name%i' % serie_i_map[key]] = str(choices[key][1] if key in choices else key)
                ydata_serie[y_key].append(value if value else 0)

        context['extra'] = {
            'x_is_date': True,
            'tag_script_js': False,
        }

        if dashboard_stats.y_axis_format:
            context['extra']['y_axis_format'] = dashboard_stats.y_axis_format

        if context['chart_type'] == 'stackedAreaChart':
            context['extra']['use_interactive_guideline'] = True

        tooltip_date_format, context['extra']['x_axis_format'] = get_dateformat(interval, context['chart_type'])

        extra_serie = {
            "tooltip": {"y_start": "", "y_end": ""},
            "date_format": tooltip_date_format,
        }

        context['values'] = {
            'x': xdata,
            'name1': interval, **ydata_serie, **names, 'extra1': extra_serie,
        }

        context['chart_container'] = "chart_container_" + graph_key
        return context


class ChartsMixin:
    def get_charts_query(self):
        query = DashboardStats.objects.order_by('graph_title').all()
        if not self.request.user.has_perm('admin_tools_stats.view_dashboardstats'):
            query = query.filter(show_to_users=True)
        return query


class AnalyticsView(LoginRequiredMixin, ChartsMixin, TemplateView):
    def get_template_names(self):
        if self.request.user.has_perm('admin_tools_stats.view_dashboardstats'):
            return 'admin_tools_stats/analytics.html'
        return 'admin_tools_stats/analytics_user.html'

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['charts'] = self.get_charts_query()
        return context_data


class AnalyticsChartView(LoginRequiredMixin, ChartsMixin, TemplateView):
    template_name = 'admin_tools_stats/analytics_chart.html'

    def get_context_data(self, *args, graph_key=None, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['chart'] = self.get_charts_query().get(graph_key=graph_key)
        return context_data
