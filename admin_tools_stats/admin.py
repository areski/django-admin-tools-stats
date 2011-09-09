from django.contrib import admin
from django.contrib import messages
from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _
from django.db.models import *
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from admin_tools_stats.models import *


class DashboardStatsCriteriaAdmin(admin.ModelAdmin):
    """Allows the administrator to view and modify certain attributes
    of a DashboardStats."""
    list_display = ('id', 'criteria_name', 'created_date')
    list_filter = ['created_date']
    ordering = ('id', )
admin.site.register(DashboardStatsCriteria, DashboardStatsCriteriaAdmin)


class DashboardStatsAdmin(admin.ModelAdmin):
    """Allows the administrator to view and modify certain attributes
    of a DashboardStats."""
    list_display = ('id', 'graph_key', 'graph_title', 'model_name', 'is_visible', 'created_date')
    list_filter = ['created_date']
    ordering = ('id', )
admin.site.register(DashboardStats, DashboardStatsAdmin)
