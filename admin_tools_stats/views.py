import csv
import logging
import time
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from datetime_truncate import truncate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.views.generic import TemplateView, View

from .models import DashboardStats, Interval, get_charts_timezone, truncate_ceiling


logger = logging.getLogger(__name__)


class AdminChartsView(TemplateView):
    template_name = "admin_tools_stats/admin_charts.js"


interval_dateformat_map_bar_chart = {
    "years": ("%Y", "%Y"),
    "quarters": ("%b %Y", "%b"),
    "months": ("%b %Y", "%b"),
    "weeks": ("%a %d %b %Y", "%W"),
    "days": ("%a %d %b %Y", "%a"),
    "hours": ("%a %d %b %Y %H:%S", "%H"),
}

interval_dateformat_map = {
    "years": ("%Y", "%Y"),
    "quarters": ("%b %Y", "%b %Y"),
    "months": ("%b %Y", "%b %Y"),
    "weeks": ("%W (%d %b %Y)", "%W"),
    "days": ("%a %d %b %Y", "%d %b %Y"),
    "hours": ("%a %d %b %Y %H:%S", "%H"),
}


def get_dateformat(interval: Interval, chart_type):
    if chart_type == "discreteBarChart":
        return interval_dateformat_map_bar_chart[interval.value]
    return interval_dateformat_map[interval.value]


def remove_multiple_keys(in_dict, entries_to_remove):
    for k in entries_to_remove:
        in_dict.pop(k, None)


class ChartDataMixin:
    def check_chart_permission(self, dashboard_stats: DashboardStats, user: User) -> bool:
        return (
            user.has_perm("admin_tools_stats.view_dashboardstats") or dashboard_stats.show_to_users
        )

    def get_chart_series_data(
        self,
        request: HttpRequest,
        dashboard_stats: DashboardStats,
        interval: Optional[Interval] = None,
    ) -> Dict[str, Any]:
        configuration: Dict[str, Union[str, List[str]]] = {
            item: request.GET[item] for item in request.GET
        }
        remove_multiple_keys(configuration, ["csrfmiddlewaretoken", "_", "graph_key"])

        selected_interval: Interval = Interval(
            configuration.pop("select_box_interval", interval) or dashboard_stats.default_time_scale
        )
        operation = configuration.pop(
            "select_box_operation", dashboard_stats.type_operation_field_name
        )
        if not isinstance(operation, str):
            operation = None
        operation_field = configuration.pop(
            "select_box_operation_field", dashboard_stats.operation_field_name
        )
        if not isinstance(operation_field, str):
            operation_field = None

        chart_type = configuration.pop("select_box_chart_type", dashboard_stats.default_chart_type)

        chart_tz = get_charts_timezone()
        time_since = datetime.strptime(str(configuration.pop("time_since")), "%Y-%m-%d")
        time_since = truncate(time_since, selected_interval.val())
        time_since = time_since.astimezone(chart_tz)

        time_until = datetime.strptime(str(configuration.pop("time_until")), "%Y-%m-%d")
        time_until = truncate_ceiling(time_until, selected_interval.val())
        time_until = time_until.astimezone(chart_tz)

        if time_since > time_until:
            raise ValueError("Time since is greater than time until")

        if dashboard_stats.cache_values:
            get_time_series = dashboard_stats.get_multi_time_series_cached
        else:
            get_time_series = dashboard_stats.get_multi_time_series

        series = get_time_series(
            configuration,
            time_since,
            time_until,
            selected_interval,
            operation,
            operation_field,
            request.user,
        )

        return {
            "series": series,
            "time_since": time_since,
            "time_until": time_until,
            "selected_interval": selected_interval,
            "chart_type": chart_type,
            "configuration": configuration,
        }


class ChartDataView(ChartDataMixin, TemplateView):
    template_name = "admin_tools_stats/chart_data.html"

    def get_context_data(
        self, *args, interval: Optional[Interval] = None, graph_key=None, **kwargs
    ):
        dashboard_stats = DashboardStats.objects.get(graph_key=graph_key)
        context = super().get_context_data(*args, **kwargs)

        if not self.check_chart_permission(dashboard_stats, self.request.user):
            context["error"] = (
                "You have no permission to view this chart. "
                "Check if you are logged in and have permission "
                "'admin_tools_stats | dashboard stats | Can view dashboard stats'"
            )
            context["graph_title"] = dashboard_stats.graph_title
            return context

        try:
            chart_data = self.get_chart_series_data(self.request, dashboard_stats, interval)
        except Exception as e:
            if "debug" in self.request.GET:
                raise
            context["error"] = str(e)
            context["graph_title"] = dashboard_stats.graph_title
            logger.exception(e)
            return context

        series = chart_data["series"]
        selected_interval = chart_data["selected_interval"]
        context["chart_type"] = chart_data["chart_type"]

        ydata_serie: Dict[str, List[int]] = {}
        names = {}
        xdata = []
        serie_i_map: Dict[str, int] = OrderedDict()
        for date in sorted(
            series.keys(),
            key=lambda d: datetime(d.year, d.month, d.day, getattr(d, "hour", 0)),
        ):
            xdata.append(int(time.mktime(date.timetuple()) * 1000))
            for key, value in series[date].items():
                if key not in serie_i_map:
                    serie_i_map[key] = len(serie_i_map)
                y_key = "y%i" % serie_i_map[key]
                if y_key not in ydata_serie:
                    ydata_serie[y_key] = []
                    names["name%i" % serie_i_map[key]] = str(key)
                ydata_serie[y_key].append(value if value else 0)

        context["extra"] = {
            "x_is_date": True,
            "tag_script_js": False,
        }

        if dashboard_stats.y_axis_format:
            context["extra"]["y_axis_format"] = dashboard_stats.y_axis_format

        if context["chart_type"] == "stackedAreaChart":
            context["extra"]["use_interactive_guideline"] = True

        tooltip_date_format, context["extra"]["x_axis_format"] = get_dateformat(
            selected_interval, context["chart_type"]
        )

        extra_serie = {
            "tooltip": {"y_start": "", "y_end": ""},
            "date_format": tooltip_date_format,
        }

        context["values"] = {
            "x": xdata,
            "name1": selected_interval,
            **ydata_serie,
            **names,
            "extra1": extra_serie,
        }

        context["chart_container"] = "chart_container_" + graph_key
        context["graph_key"] = graph_key
        return context


class ChartDataCSVView(ChartDataMixin, View):
    def get(self, request, graph_key=None):
        dashboard_stats = DashboardStats.objects.get(graph_key=graph_key)

        if not self.check_chart_permission(dashboard_stats, request.user):
            return HttpResponse("Permission denied", status=403)

        chart_data = self.get_chart_series_data(request, dashboard_stats)
        series = chart_data["series"]
        time_since = chart_data["time_since"]
        time_until = chart_data["time_until"]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{graph_key}_{time_since.strftime("%Y%m%d")}_'
            f'{time_until.strftime("%Y%m%d")}.csv"'
        )

        writer = csv.writer(response)

        serie_keys = set()
        for date_data in series.values():
            serie_keys.update(date_data.keys())
        serie_keys = [key for key in serie_keys if key is not None]
        serie_keys = sorted(serie_keys, key=str)

        header = ["Date"] + [str(key) for key in serie_keys]
        writer.writerow(header)

        for date in sorted(
            series.keys(),
            key=lambda d: datetime(d.year, d.month, d.day, getattr(d, "hour", 0)),
        ):
            date_str = date.strftime("%Y-%m-%d %H:%M:%S")
            row = [date_str]
            for key in serie_keys:
                value = series[date].get(key, 0)
                row.append(value if value else 0)
            writer.writerow(row)

        return response


class ChartsMixin:
    def get_charts_query(self):
        query = DashboardStats.objects.order_by("graph_title").all()
        if not self.request.user.has_perm("admin_tools_stats.view_dashboardstats"):
            query = query.filter(show_to_users=True)
        return query


class AnalyticsView(LoginRequiredMixin, ChartsMixin, TemplateView):
    def get_template_names(self):
        if self.request.user.has_perm("admin_tools_stats.view_dashboardstats"):
            return "admin_tools_stats/analytics.html"
        return "admin_tools_stats/analytics_user.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["nonuser_charts"] = self.get_charts_query().filter(show_to_users=False)
        context_data["charts"] = self.get_charts_query()
        return context_data


class AnalyticsChartView(LoginRequiredMixin, ChartsMixin, TemplateView):
    template_name = "admin_tools_stats/analytics_chart.html"

    def get_context_data(self, *args, graph_key=None, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data["chart"] = self.get_charts_query().get(graph_key=graph_key)
        return context_data
