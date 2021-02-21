# Generated by Django 3.0.10 on 2020-09-11 12:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_tools_stats', '0007_auto_20200205_1054'),
    ]

    operations = [
        migrations.AddField(
            model_name='criteriatostatsm2m',
            name='default_option',
            field=models.CharField(blank=True, default='', help_text='Works only with Chart filter criteri', max_length=255, verbose_name='Default filter criteria option'),
        ),
        migrations.AddField(
            model_name='dashboardstats',
            name='default_multiseries_criteria',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='default_choices_stats', to='admin_tools_stats.CriteriaToStatsM2M'),
        ),
    ]
