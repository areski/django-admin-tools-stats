
from django.urls import path

from .views import ChartDataView


urlpatterns = [
    path('chart_data/', ChartDataView.as_view(), name='chart-data'),  #Only to get the base address in template, will need parameters
    path('chart_data/<str:interval>/<str:graph_key>/', ChartDataView.as_view(), name='chart-data'),
    path('chart_data/<str:interval>/<str:graph_key>/<str:select_box_value>/', ChartDataView.as_view(), name='chart-data'),
]
