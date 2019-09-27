from django.conf import settings
from django.utils.module_loading import import_string
from django.views.generic import TemplateView


class ChartDataView(TemplateView):
    template_name = 'admin_tools_stats/chart_data.html'

    cache_cache_name = "pages"

    def get_context_data(self, *args, interval=None, graph_key=None, select_box_value='', **kwargs):
        context = super().get_context_data(*args, **kwargs)
        DashboardChart = import_string(getattr(settings, 'ADMIN_TOOLS_STATS_CHART_APP', 'admin_tools_stats.modules.DashboardChart'))
        module = DashboardChart(
            'today'.title(),
            interval=interval,
            require_chart_jscss=False,
            graph_key=graph_key,
            **{"select_box_" + graph_key: select_box_value},
        )
        module.init_with_context_ajax({'request': self.request})
        context['module'] = module
        return context
