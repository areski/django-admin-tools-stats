import time
from datetime import datetime

from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

import pytz

from .models import DashboardStats


class AdminChartsView(TemplateView):
    template_name = 'admin_tools_stats/admin_charts.js'


chart_type = 'discreteBarChart'
interval_dateformat_map = {
    'years': ("%Y", "%Y"),
    'weeks': ("%b %Y", "%b"),
    'months': ("%b %Y", "%b"),
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
        try:
            time_since = datetime.strptime(self.request.GET.get('time_since', None), '%Y-%m-%d')
            time_until = datetime.strptime(self.request.GET.get('time_until', None), '%Y-%m-%d')
        except ValueError:
            return context

        # TODO: current timezone doesn't work for years with queryset stats
        # current_tz = timezone.get_current_timezone()
        current_tz = pytz.utc
        time_since = current_tz.localize(time_since)
        time_until = current_tz.localize(time_until)
        time_until = time_until.replace(hour=23, minute=59)

        dashboard_stats = DashboardStats.objects.get(graph_key=graph_key)
        data = dashboard_stats.get_time_series(self.request, time_since, time_until, interval)
        xdata = []
        ydata = []
        for data_date in data:
            start_time = int(time.mktime(data_date[0].timetuple()) * 1000)
            xdata.append(start_time)
            ydata.append(data_date[1])

        context['extra'] = {
            'x_is_date': True,
            'tag_script_js': False,
        }

        tooltip_date_format, context['extra']['x_axis_format'] = interval_dateformat_map[interval]

        extra_serie = {"tooltip": {"y_start": "", "y_end": ""},
                       "date_format": tooltip_date_format}

        context['values'] = {
            'x': xdata,
            'name1': interval, 'y1': ydata, 'extra1': extra_serie,
        }

        context['chart_container'] = "chart_container_" + graph_key
        context['chart_type'] = chart_type
        return context
