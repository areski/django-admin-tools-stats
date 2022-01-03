# -*- coding: utf-8 -*-
from django.db import models
from south.db import db
from south.utils import datetime_utils as datetime
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding field 'DashboardStats.sum_field_name'
        db.add_column(
            "dashboard_stats",
            "sum_field_name",
            self.gf("django.db.models.fields.CharField")(max_length=90, null=True, blank=True),
            keep_default=False,
        )

    def backwards(self, orm):
        # Deleting field 'DashboardStats.sum_field_name'
        db.delete_column("dashboard_stats", "sum_field_name")

    models = {
        "admin_tools_stats.dashboardstats": {
            "Meta": {"object_name": "DashboardStats", "db_table": "u'dashboard_stats'"},
            "created_date": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now_add": "True", "blank": "True"},
            ),
            "criteria": (
                "django.db.models.fields.related.ManyToManyField",
                [],
                {
                    "symmetrical": "False",
                    "to": "orm['admin_tools_stats.DashboardStatsCriteria']",
                    "null": "True",
                    "blank": "True",
                },
            ),
            "date_field_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "90"},
            ),
            "graph_key": (
                "django.db.models.fields.CharField",
                [],
                {"unique": "True", "max_length": "90"},
            ),
            "graph_title": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "90", "db_index": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "is_visible": (
                "django.db.models.fields.BooleanField",
                [],
                {"default": "True"},
            ),
            "model_app_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "90"},
            ),
            "model_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "90"},
            ),
            "sum_field_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "90", "null": "True", "blank": "True"},
            ),
            "updated_date": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now": "True", "blank": "True"},
            ),
        },
        "admin_tools_stats.dashboardstatscriteria": {
            "Meta": {
                "object_name": "DashboardStatsCriteria",
                "db_table": "u'dash_stats_criteria'",
            },
            "created_date": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now_add": "True", "blank": "True"},
            ),
            "criteria_dynamic_mapping": (
                "jsonfield.fields.JSONField",
                [],
                {"null": "True", "blank": "True"},
            ),
            "criteria_fix_mapping": (
                "jsonfield.fields.JSONField",
                [],
                {"null": "True", "blank": "True"},
            ),
            "criteria_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "90", "db_index": "True"},
            ),
            "dynamic_criteria_field_name": (
                "django.db.models.fields.CharField",
                [],
                {"max_length": "90", "null": "True", "blank": "True"},
            ),
            "id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
            "updated_date": (
                "django.db.models.fields.DateTimeField",
                [],
                {"auto_now": "True", "blank": "True"},
            ),
        },
    }

    complete_apps = ["admin_tools_stats"]
