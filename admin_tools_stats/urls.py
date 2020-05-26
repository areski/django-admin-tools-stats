
from django.urls import path

from .views import AdminChartsView, AnalyticsView, ChartDataView


urlpatterns = [
    path('admin_charts.js', AdminChartsView.as_view(content_type='application/javascript'), name='admin-charts'),
    path('chart_data/', ChartDataView.as_view(), name='chart-data'),  # Only to get the base address in template, will need parameters
    path('chart_data/<str:graph_key>/', ChartDataView.as_view(), name='chart-data'),
    path('analytics/', AnalyticsView.as_view(), name='chart-analytics'),
]
