#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from admin_tools_stats.app_label_renamer import AppLabelRenamer
from admin_tools_stats.models import CriteriaToStatsM2M, DashboardStats, DashboardStatsCriteria

AppLabelRenamer(native_app_label=u'admin_tools_stats', app_label=_('Admin Tools Stats')).main()


class DashboardStatsCriteriaAdmin(admin.ModelAdmin):
    """
    Allows the administrator to view and modify certain attributes
    of a DashboardStats.
    """
    list_display = ('id', 'criteria_name', 'created_date')
    list_filter = ['created_date']
    search_fields = ('criteria_name',)
    ordering = ('id', )
    save_as = True


admin.site.register(DashboardStatsCriteria, DashboardStatsCriteriaAdmin)


class DashboardStatsCriteriaInline(admin.TabularInline):
    model = CriteriaToStatsM2M
    readonly_fields = ('criteria__dynamic_criteria_field_name',)
    fields = ('criteria', 'order', 'prefix', 'criteria__dynamic_criteria_field_name', 'use_as')
    autocomplete_fields = ('criteria',)
    extra = 0

    def criteria__dynamic_criteria_field_name(self, obj):
        return obj.criteria.dynamic_criteria_field_name


class DashboardStatsAdmin(admin.ModelAdmin):
    """
    Allows the administrator to view and modify certain attributes
    of a DashboardStats.
    """
    list_display = ('id', 'graph_key', 'graph_title', 'model_name', 'distinct', 'type_operation_field_name',
                    'is_visible', 'created_date', 'date_field_name', 'operation_field_name', 'default_chart_type')
    list_filter = ['created_date']
    exclude = ('criteria',)
    inlines = [DashboardStatsCriteriaInline]
    ordering = ('id', )
    save_as = True


admin.site.register(DashboardStats, DashboardStatsAdmin)
