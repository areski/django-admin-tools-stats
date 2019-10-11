import time
from collections import OrderedDict
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

import pytz

from .models import DashboardStats


class AdminChartsView(TemplateView):
    template_name = 'admin_tools_stats/admin_charts.js'

    def get_context_data(self, *args, interval=None, graph_key=None, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['chart_height'] = 300
        context['chart_width'] = '100%'
        return context


interval_dateformat_map = {
    'years': ("%Y", "%Y"),
    'months': ("%b %Y", "%b"),
    'weeks': ("%a %d %b %Y", "%W"),
    'days': ("%a %d %b %Y", "%a"),
    'hours': ("%a %d %b %Y %H:%S", "%H"),
}


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class ChartDataView(TemplateView):
    template_name = 'admin_tools_stats/chart_data.html'

    cache_cache_name = "pages"

    def get_context_data(self, *args, interval=None, graph_key=None, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        interval = self.request.GET.get('select_box_interval', interval)
        context['chart_type'] = self.request.GET.get('select_box_chart_type', interval)
        try:
            time_since = datetime.strptime(self.request.GET.get('time_since', None), '%Y-%m-%d')
            time_until = datetime.strptime(self.request.GET.get('time_until', None), '%Y-%m-%d')
        except ValueError:
            return context

        # TODO: current timezone doesn't work for years with queryset stats
        # current_tz = timezone.get_current_timezone()
        current_tz = pytz.utc
        dashboard_stats = DashboardStats.objects.get(graph_key=graph_key)

        if settings.USE_TZ:
            time_since = current_tz.localize(time_since)
            time_until = current_tz.localize(time_until)
        time_until = time_until.replace(hour=23, minute=59)

        series = dashboard_stats.get_multi_time_series(self.request.GET, time_since, time_until, interval, self.request)
        criteria = dashboard_stats.get_multi_series_criteria(self.request.GET)
        if criteria:
            choices = criteria.get_dynamic_choices(criteria, dashboard_stats)
        else:
            choices = {}

        ydata_serie = {}
        names = {}
        xdata = []
        serie_i_map = OrderedDict()
        for date in sorted(series.keys()):
            xdata.append(int(time.mktime(date.timetuple()) * 1000))
            for key, value in series[date].items():
                if key not in serie_i_map:
                    serie_i_map[key] = len(serie_i_map)
                y_key = 'y%i' % serie_i_map[key]
                if y_key not in ydata_serie:
                    ydata_serie[y_key] = []
                    names['name%i' % serie_i_map[key]] = str(choices[key][1] if key in choices else key)
                ydata_serie[y_key].append(value)

        context['extra'] = {
            'x_is_date': True,
            'tag_script_js': False,
        }

        tooltip_date_format, context['extra']['x_axis_format'] = interval_dateformat_map[interval]

        extra_serie = {"tooltip": {"y_start": "", "y_end": ""},
                       "date_format": tooltip_date_format}

        context['values'] = {
            'x': xdata,
            'name1': interval, **ydata_serie, **names, 'extra1': extra_serie,
        }

        context['chart_container'] = "chart_container_" + graph_key
        return context
