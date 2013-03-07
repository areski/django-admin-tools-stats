from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from admin_tools_stats.models import DashboardStatsCriteria, DashboardStats
from common.app_label_renamer import AppLabelRenamer
AppLabelRenamer(native_app_label=u'admin_tools_stats', app_label=_('Admin Tools Stats')).main()


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
