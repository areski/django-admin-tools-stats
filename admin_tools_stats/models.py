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
from datetime import timedelta

try:  # Python 3
    from django.utils.encoding import force_text
except ImportError:  # Python 2
    from django.utils.encoding import force_unicode as force_text
from django.apps import apps
from django.contrib import messages
from django.core.exceptions import FieldError, ValidationError
from django.db import models
from django.db.models.aggregates import Avg, Count, Max, Min, StdDev, Sum, Variance
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

import jsonfield.fields

from qsstats import QuerySetStats


operation = (
    ('DistinctCount', 'DistinctCount'),
    ('Count', 'Count'),
    ('Sum', 'Sum'),
    ('Avg', 'Avg'),
    ('Max', 'Max'),
    ('Min', 'Min'),
    ('StdDev', 'StdDev'),
    ('Variance', 'Variance'),
)


@python_2_unicode_compatible
class DashboardStatsCriteria(models.Model):
    """
    To configure criteria for dashboard graphs

    **Attributes**:

        * ``criteria_name`` - Unique word .
        * ``criteria_fix_mapping`` - JSON data key-value pairs.
        * ``dynamic_criteria_field_name`` - Dynamic criteria field.
        * ``criteria_dynamic_mapping`` - JSON data key-value pairs.
        * ``created_date`` - record created date.
        * ``updated_date`` - record updated date.

    **Name of DB table**: dash_stats_criteria
    """
    criteria_name = models.CharField(max_length=90, db_index=True,
                                     verbose_name=_('criteria name'),
                                     help_text=_("it needs to be one word unique. Ex. status, yesno"))
    criteria_fix_mapping = jsonfield.fields.JSONField(
        null=True, blank=True,
        verbose_name=_("fixed criteria / value"),
        help_text=_("a JSON dictionary of key-value pairs that will be used for the criteria"))
    dynamic_criteria_field_name = models.CharField(
        max_length=90, blank=True, null=True,
        verbose_name=_("dynamic criteria field name"),
        help_text=_("ex. for call records - disposition"))
    criteria_dynamic_mapping = jsonfield.fields.JSONField(
        null=True, blank=True,
        verbose_name=_("dynamic criteria / value"),
        help_text=_(
            "a JSON dictionary of key-value pairs that will be used for the criteria"
            " Ex. \"{'false': 'Inactive', 'true': 'Active'}\"",
        ),
    )
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "admin_tools_stats"
        db_table = u'dash_stats_criteria'
        verbose_name = _("dashboard stats criteria")
        verbose_name_plural = _("dashboard stats criteria")

    def __str__(self):
            return u"%s" % self.criteria_name


@python_2_unicode_compatible
class DashboardStats(models.Model):
    """To configure graphs for dashboard

    **Attributes**:

        * ``graph_key`` - unique graph name.
        * ``graph_title`` - graph title.
        * ``model_app_name`` - App name of model.
        * ``model_name`` - model name.
        * ``date_field_name`` - Date field of model_name.
        * ``criteria`` - many-to-many relationship.
        * ``is_visible`` - enable/disable.
        * ``created_date`` - record created date.
        * ``updated_date`` - record updated date.

    **Name of DB table**: dashboard_stats
    """
    graph_key = models.CharField(unique=True, max_length=90,
                                 verbose_name=_('graph identifier'),
                                 help_text=_("it needs to be one word unique. ex. auth, mygraph"))
    graph_title = models.CharField(max_length=90, db_index=True,
                                   verbose_name=_('graph title'),
                                   help_text=_("heading title of graph box"))
    model_app_name = models.CharField(max_length=90, verbose_name=_('app name'),
                                      help_text=_("ex. auth / dialer_cdr"))
    model_name = models.CharField(max_length=90, verbose_name=_('model name'),
                                  help_text=_("ex. User"))
    date_field_name = models.CharField(max_length=90, verbose_name=_("date field name"),
                                       help_text=_("ex. date_joined, invitation__invitation_date"))
    user_field_name = models.CharField(max_length=90, verbose_name=_("user field name"),
                                       null=True, blank=True,
                                       help_text=_("ex. owner, invitation__owner"))
    operation_field_name = models.CharField(max_length=90, verbose_name=_("Operate field name"),
                                      null=True, blank=True,
                                      help_text=_("The field you want to aggregate, ex. amount, salaries__total_income"))
    type_operation_field_name = models.CharField(max_length=90, verbose_name=_("Choose Type operation"),
                                      null=True, blank=True, choices=operation,
                                      help_text=_("choose the type operation what you want to aggregate, ex. Sum"))
    criteria = models.ManyToManyField(DashboardStatsCriteria, blank=True)
    is_visible = models.BooleanField(default=True, verbose_name=_('visible'))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "admin_tools_stats"
        db_table = u'dashboard_stats'
        verbose_name = _("dashboard stats")
        verbose_name_plural = _("dashboard stats")

    def clean(self, *args, **kwargs):
        errors = {}
        model = None
        try:
            apps.get_app_config(self.model_app_name)
        except LookupError as e:
            errors['model_app_name'] = str(e)

        try:
            model = apps.get_model(self.model_app_name, self.model_name)
        except LookupError as e:
            errors['model_name'] = str(e)

        try:
            if model and self.operation_field_name:
                model.objects.all().query.resolve_ref(self.operation_field_name)
        except FieldError as e:
            errors['operation_field_name'] = str(e)

        try:
            if model and self.date_field_name:
                model.objects.all().query.resolve_ref(self.date_field_name)
        except FieldError as e:
            errors['date_field_name'] = str(e)

        raise ValidationError(errors)
        return super(DashboardStats, self).clean(*args, **kwargs)

    def get_time_series(self, request, time_since, time_until, interval):
        """ Get the stats time series """
        try:
            model_name = apps.get_model(self.model_app_name, self.model_name)
            kwargs = {}
            if not request.user.is_superuser and self.user_field_name:
                kwargs[self.user_field_name] = request.user
            for i in self.criteria.all():
                # fixed mapping value passed info kwargs
                if i.criteria_fix_mapping:
                    for key in i.criteria_fix_mapping:
                        # value => i.criteria_fix_mapping[key]
                        kwargs[key] = i.criteria_fix_mapping[key]

                # dynamic mapping value passed info kwargs
                dynamic_key = "select_box_dynamic_%i" % i.id
                if dynamic_key in request.GET:
                    if request.GET[dynamic_key] != '':
                        kwargs[i.dynamic_criteria_field_name] = request.GET[dynamic_key]

            aggregate = None
            if self.type_operation_field_name and self.operation_field_name:
                operation = {
                    'DistinctCount': Count(self.operation_field_name, distinct=True),
                    'Count': Count(self.operation_field_name),
                    'Sum': Sum(self.operation_field_name),
                    'Avg': Avg(self.operation_field_name),
                    'StdDev': StdDev(self.operation_field_name),
                    'Max': Max(self.operation_field_name),
                    'Min': Min(self.operation_field_name),
                    'Variance': Variance(self.operation_field_name),
                }
                aggregate = operation[self.type_operation_field_name]

            stats = QuerySetStats(model_name.objects.filter(**kwargs).distinct(),
                                  self.date_field_name, aggregate)
            return stats.time_series(time_since, time_until, interval)
        except (LookupError, FieldError, TypeError) as e:
            self.error_message = str(e)
            messages.add_message(request, messages.ERROR, "%s dashboard: %s" % (self.graph_title, str(e)))

    def get_control_form(self):
        """ Get content of the ajax control form """
        temp = ''
        for i in self.criteria.all():
            dy_map = i.criteria_dynamic_mapping
            if dy_map:
                temp += i.criteria_name + ': <select class="chart-input dynamic_criteria_select_box" name="select_box_dynamic_%i" >' % i.id
                for key in dict(dy_map):
                    temp += '<option value="' + key + '">' + dy_map[key] + '</option>'
                temp += '</select>'

        temp += '<input type="hidden" class="hidden_graph_key" name="graph_key" value="%s">' % self.graph_key

        temp += 'Scale: <select class="chart-input select_box_interval" name="select_box_interval" >'
        for interval in ('hours', 'days', 'weeks', 'months', 'years'):
            selected_str = 'selected=selected' if interval == 'days' else ''
            temp += '<option class="chart-input" value="' + interval + '" ' + selected_str + '>' + interval + '</option>'
        temp += '</select>'

        temp += 'Since: <input class="chart-input select_box_date_since" type="date" name="time_since" value="%s">' % \
            (now() - timedelta(days=21)).strftime('%Y-%m-%d')
        temp += 'Until: <input class="chart-input select_box_date_since" type="date" name="time_until" value="%s">' % \
            now().strftime('%Y-%m-%d')

        chart_types = (
            ('discreteBarChart',        'Bar'),
            ('lineChart',               'Line'),
            ('multiBarChart',           'Multi Bar'),
            ('pieChart',                'Pie'),
            ('stackedAreaChart',        'Stacked Area'),
            ('multiBarHorizontalChart', 'Multi Bar Horizontal'),
            ('linePlusBarChart',        'Line Plus Bar'),
            ('scatterChart',            'Scatter'),
            ('cumulativeLineChart',     'Cumulative Line'),
            ('lineWithFocusChart',      'Line With Focus'),
        )
        temp += 'Chart: <select class="chart-input select_box_chart_type" name="select_box_chart_type" >'
        for chart_type_str, chart_type_name in chart_types:
            selected_str = 'selected=selected' if chart_type_str == 'discreteBarChart' else ''
            temp += '<option class="chart-input" value="' + chart_type_str + '" ' + selected_str + '>' + chart_type_name + '</option>'
        temp += '</select>'

        return mark_safe(force_text(temp))

    def __str__(self):
            return u"%s" % self.graph_key

    @classmethod
    def get_active_graph(cls):
        """Returns active graphs"""
        return DashboardStats.objects.filter(is_visible=1).prefetch_related('criteria')
