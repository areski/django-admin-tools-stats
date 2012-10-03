from django.contrib import admin
from admin_tools_stats.models import DashboardStatsCriteria, DashboardStats


class DashboardStatsCriteriaAdmin(admin.ModelAdmin):
    """
    Allows the administrator to view and modify certain attributes
    of a DashboardStats.
    """
    list_display = ('id', 'criteria_name', 'created_date')
    list_filter = ['created_date']
    ordering = ('id', )

admin.site.register(DashboardStatsCriteria, DashboardStatsCriteriaAdmin)


class DashboardStatsAdmin(admin.ModelAdmin):
    """
    Allows the administrator to view and modify certain attributes
    of a DashboardStats.
    """
    list_display = ('id', 'graph_key', 'graph_title', 'model_name',
                    'is_visible', 'created_date')
    list_filter = ['created_date']
    ordering = ('id', )

admin.site.register(DashboardStats, DashboardStatsAdmin)
