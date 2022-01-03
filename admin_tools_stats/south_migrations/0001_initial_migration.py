# -*- coding: utf-8 -*-
from django.db import models
from south.db import db
from south.utils import datetime_utils as datetime
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'DashboardStatsCriteria'
        db.create_table(
            "dash_stats_criteria",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "criteria_name",
                    self.gf("django.db.models.fields.CharField")(max_length=90, db_index=True),
                ),
                (
                    "criteria_fix_mapping",
                    self.gf("jsonfield.fields.JSONField")(null=True, blank=True),
                ),
                (
                    "dynamic_criteria_field_name",
                    self.gf("django.db.models.fields.CharField")(
                        max_length=90, null=True, blank=True
                    ),
                ),
                (
                    "criteria_dynamic_mapping",
                    self.gf("jsonfield.fields.JSONField")(null=True, blank=True),
                ),
                (
                    "created_date",
                    self.gf("django.db.models.fields.DateTimeField")(auto_now_add=True, blank=True),
                ),
                (
                    "updated_date",
                    self.gf("django.db.models.fields.DateTimeField")(auto_now=True, blank=True),
                ),
            ),
        )
        db.send_create_signal("admin_tools_stats", ["DashboardStatsCriteria"])

        # Adding model 'DashboardStats'
        db.create_table(
            "dashboard_stats",
            (
                ("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
                (
                    "graph_key",
                    self.gf("django.db.models.fields.CharField")(unique=True, max_length=90),
                ),
                (
                    "graph_title",
                    self.gf("django.db.models.fields.CharField")(max_length=90, db_index=True),
                ),
                (
                    "model_app_name",
                    self.gf("django.db.models.fields.CharField")(max_length=90),
                ),
                (
                    "model_name",
                    self.gf("django.db.models.fields.CharField")(max_length=90),
                ),
                (
                    "date_field_name",
                    self.gf("django.db.models.fields.CharField")(max_length=90),
                ),
                (
                    "is_visible",
                    self.gf("django.db.models.fields.BooleanField")(default=True),
                ),
                (
                    "created_date",
                    self.gf("django.db.models.fields.DateTimeField")(auto_now_add=True, blank=True),
                ),
                (
                    "updated_date",
                    self.gf("django.db.models.fields.DateTimeField")(auto_now=True, blank=True),
                ),
            ),
        )
        db.send_create_signal("admin_tools_stats", ["DashboardStats"])

        # Adding M2M table for field criteria on 'DashboardStats'
        m2m_table_name = db.shorten_name("dashboard_stats_criteria")
        db.create_table(
            m2m_table_name,
            (
                (
                    "id",
                    models.AutoField(verbose_name="ID", primary_key=True, auto_created=True),
                ),
                (
                    "dashboardstats",
                    models.ForeignKey(orm["admin_tools_stats.dashboardstats"], null=False),
                ),
                (
                    "dashboardstatscriteria",
                    models.ForeignKey(orm["admin_tools_stats.dashboardstatscriteria"], null=False),
                ),
            ),
        )
        db.create_unique(m2m_table_name, ["dashboardstats_id", "dashboardstatscriteria_id"])

    def backwards(self, orm):
        # Deleting model 'DashboardStatsCriteria'
        db.delete_table("dash_stats_criteria")

        # Deleting model 'DashboardStats'
        db.delete_table("dashboard_stats")

        # Removing M2M table for field criteria on 'DashboardStats'
        db.delete_table(db.shorten_name("dashboard_stats_criteria"))

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
