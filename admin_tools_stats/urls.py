from django.urls import path

from . import views


urlpatterns = [
    path(
        "admin_charts.js",
        views.AdminChartsView.as_view(content_type="application/javascript"),
        name="admin-charts",
    ),
    path(
        "chart_data/", views.ChartDataView.as_view(), name="chart-data"
    ),  # Only to get the base address in template, will need parameters
    path("chart_data/<str:graph_key>/", views.ChartDataView.as_view(), name="chart-data"),
    path("analytics/", views.AnalyticsView.as_view(), name="chart-analytics"),
    path(
        "analytics/chart/<str:graph_key>/",
        views.AnalyticsChartView.as_view(),
        name="chart-analytics",
    ),
    path(  # Only to get the base address in template, will need parameters
        "analytics/chart/",
        views.AnalyticsChartView.as_view(),
        name="chart-analytics-without-key",
    ),
]
