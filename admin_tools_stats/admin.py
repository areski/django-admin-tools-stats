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

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from admin_tools_stats.app_label_renamer import AppLabelRenamer
from admin_tools_stats.models import (
    CachedValue,
    CriteriaToStatsM2M,
    DashboardStats,
    DashboardStatsCriteria,
)


AppLabelRenamer(native_app_label="admin_tools_stats", app_label=_("Admin Tools Stats")).main()


@admin.register(DashboardStatsCriteria)
class DashboardStatsCriteriaAdmin(admin.ModelAdmin):
    """
    Allows the administrator to view and modify certain attributes
    of a DashboardStats.
    """

    list_display = (
        "id",
        "criteria_name",
        "criteria_name",
        "dynamic_criteria_field_name",
        "criteria_dynamic_mapping_preview",
    )
    list_filter = ["created_date"]
    readonly_fields = (
        "created_date",
        "updated_date",
    )
    search_fields = ("criteria_name",)
    ordering = ("id",)
    save_as = True


class DashboardStatsCriteriaInline(admin.TabularInline):
    model = CriteriaToStatsM2M
    readonly_fields = (
        "criteria__dynamic_criteria_field_name",
        "criteria__criteria_dynamic_mapping_preview",
    )
    fields = (
        "criteria",
        "order",
        "use_as",
        "default_option",
        "choices_based_on_time_range",
        "recalculate",
        "count_limit",
        "prefix",
        "criteria__dynamic_criteria_field_name",
        "criteria__criteria_dynamic_mapping_preview",
    )
    autocomplete_fields = ("criteria",)
    extra = 0

    def criteria__dynamic_criteria_field_name(self, obj):
        return format_html(
            "<strong>{}</strong>{}",
            str(obj.prefix or ""),
            str(obj.criteria.dynamic_criteria_field_name or ""),
        )

    def criteria__criteria_dynamic_mapping_preview(self, obj):
        return obj.criteria.criteria_dynamic_mapping_preview()


class DashboardStatsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["default_multiseries_criteria"].queryset = CriteriaToStatsM2M.objects.filter(
            stats=self.instance,
        )


@admin.register(DashboardStats)
class DashboardStatsAdmin(admin.ModelAdmin):
    """
    Allows the administrator to view and modify certain attributes
    of a DashboardStats.
    """

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "graph_key",
                    "graph_title",
                    ("model_app_name", "model_name", "date_field_name"),
                    ("operation_field_name", "distinct"),
                    ("user_field_name", "show_to_users"),
                    ("allowed_type_operation_field_name", "type_operation_field_name"),
                    ("allowed_chart_types", "default_chart_type"),
                    (
                        "allowed_time_scales",
                        "default_time_scale",
                        "default_time_period",
                    ),
                    "y_axis_format",
                    "default_multiseries_criteria",
                    "is_visible",
                    "cache_values",
                ),
            },
        ),
    )
    list_display = (
        "id",
        "graph_key",
        "analytics_link",
        "graph_title",
        "model_name",
        "distinct",
        "type_operation_field_name",
        "is_visible",
        "show_to_users",
        "cache_values",
        "created_date",
        "date_field_name",
        "operation_field_name",
        "default_chart_type",
    )
    list_filter = [
        "created_date",
        "is_visible",
        "show_to_users",
        "cache_values",
    ]
    exclude = ("criteria",)
    inlines = [DashboardStatsCriteriaInline]
    save_as = True
    form = DashboardStatsForm

    def analytics_link(self, obj):
        return format_html(
            "<a href='{url}?show={key}' target='_blank'>A</a>",
            url=reverse("chart-analytics"),
            key=obj.graph_key,
        )


@admin.register(CachedValue)
class CachedValueAdmin(admin.ModelAdmin):
    list_display = (
        "stats",
        "date",
        "value",
        "operation",
        "operation_field_name",
        "filtered_value",
        "time_scale",
        "multiple_series_choice",
        "is_final",
    )
    list_filter = (
        "stats",
        "operation",
        "operation_field_name",
        "filtered_value",
        "time_scale",
        "is_final",
        "multiple_series_choice",
        "stats__cache_values",
    )
