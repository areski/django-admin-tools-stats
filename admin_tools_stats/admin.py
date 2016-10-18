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
from admin_tools_stats.models import DashboardStatsCriteria, DashboardStats
from admin_tools_stats.app_label_renamer import AppLabelRenamer
AppLabelRenamer(native_app_label=u'admin_tools_stats', app_label=_('Admin Tools Stats')).main()


class DashboardStatsCriteriaAdmin(admin.ModelAdmin):
    """
    Allows the administrator to view and modify certain attributes
    of a DashboardStats.
    """
    list_display = ('id', 'criteria_name', 'created_date')
    list_filter = ['created_date']
    ordering = ('id', )
    save_as = True

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
    save_as = True

admin.site.register(DashboardStats, DashboardStatsAdmin)
