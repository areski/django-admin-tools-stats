# Generated by Django 4.0.8 on 2022-11-02 22:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_tools_stats', '0016_dashboardstats_cache_values'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dashboardstats',
            options={'permissions': (('view_dashboard_stats', 'Can view dashboard charts'),), 'verbose_name': 'dashboard stats', 'verbose_name_plural': 'dashboard stats'},
        ),
        migrations.AlterField(
            model_name='cachedvalue',
            name='time_scale',
            field=models.CharField(choices=[('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('quarters', 'Quarters'), ('years', 'Years')], default='days', max_length=90, verbose_name='Time scale'),
        ),
        migrations.AlterField(
            model_name='dashboardstats',
            name='cache_values',
            field=models.BooleanField(default=False, help_text="If chart's values are cached, you will always get cached values, unless you pres reload/reload_all button", verbose_name='cache charts values'),
        ),
    ]
