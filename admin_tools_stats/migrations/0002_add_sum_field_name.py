# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'DashboardStats.sum_field_name'
        db.add_column(u'dashboard_stats', 'sum_field_name',
                      self.gf('django.db.models.fields.CharField')(max_length=90, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'DashboardStats.sum_field_name'
        db.delete_column(u'dashboard_stats', 'sum_field_name')


    models = {
        u'admin_tools_stats.dashboardstats': {
            'Meta': {'object_name': 'DashboardStats', 'db_table': "u'dashboard_stats'"},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'criteria': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['admin_tools_stats.DashboardStatsCriteria']", 'null': 'True', 'blank': 'True'}),
            'date_field_name': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'graph_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '90'}),
            'graph_title': ('django.db.models.fields.CharField', [], {'max_length': '90', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'model_app_name': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'model_name': ('django.db.models.fields.CharField', [], {'max_length': '90'}),
            'sum_field_name': ('django.db.models.fields.CharField', [], {'max_length': '90', 'null': 'True', 'blank': 'True'}),
            'updated_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'admin_tools_stats.dashboardstatscriteria': {
            'Meta': {'object_name': 'DashboardStatsCriteria', 'db_table': "u'dash_stats_criteria'"},
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'criteria_dynamic_mapping': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'criteria_fix_mapping': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'criteria_name': ('django.db.models.fields.CharField', [], {'max_length': '90', 'db_index': 'True'}),
            'dynamic_criteria_field_name': ('django.db.models.fields.CharField', [], {'max_length': '90', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['admin_tools_stats']