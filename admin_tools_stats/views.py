import pytz
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string
from django.views.generic import TemplateView
from django.utils.timezone import now


class AdminChartsView(TemplateView):
    template_name = 'admin_tools_stats/admin_charts.js'


class ChartDataView(TemplateView):
    template_name = 'admin_tools_stats/chart_data.html'

    cache_cache_name = "pages"

    def get_context_data(self, *args, interval=None, graph_key=None, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        interval = self.request.GET.get('select_box_interval', interval)
        time_since = datetime.strptime(self.request.GET.get('time_since', None), '%Y-%m-%d')
        time_since = pytz.utc.localize(time_since)
        time_until = datetime.strptime(self.request.GET.get('time_until', None), '%Y-%m-%d')
        time_until = pytz.utc.localize(time_until)
        DashboardChart = import_string(getattr(settings, 'ADMIN_TOOLS_STATS_CHART_APP', 'admin_tools_stats.modules.DashboardChart'))
        module = DashboardChart(
            'today'.title(),
            interval=interval,
            time_since=time_since,
            time_until=time_until,
            require_chart_jscss=False,
            graph_key=graph_key,
        )
        module.init_with_context_ajax({'request': self.request})
        context['module'] = module
        return context
