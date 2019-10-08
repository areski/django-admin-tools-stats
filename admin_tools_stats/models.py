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
from cache_utils.decorators import cached

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
time_scales = (
    ('hours', 'Hours'),
    ('days', 'Days'),
    ('weeks', 'Weeks'),
    ('months', 'Months'),
    ('years', 'Years'),
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
            mark_safe(
                "a JSON dictionary with records in two following possible formats:"
                '<br/>"key_value": "name"'
                '<br/>"key": [value, "name"]'
                '<br/>use blank key for no filter'
                '<br/>Example:'
                '<br/><pre>{'
                '<br/>  "": [null, "All"],'
                '<br/>  "True": [true, "True"],'
                '<br/>  "False": [false, "False"]'
                '<br/>}</pre>'
                "<br/>Left blank to exploit all choices of CharField with choices",
            ),
        ),
    )
    use_as = models.CharField(
        max_length=90,
        blank=False,
        null=False,
        verbose_name=_("Use dynamic criteria as"),
        choices=(
            ('chart_filter', 'Chart filter'),
            ('multiple_series', 'Multiple series'),
        ),
        default='chart_filter',
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

    # The slef argument is here just because of this bug: https://github.com/infoscout/django-cache-utils/issues/19
    @cached(60 * 5)
    def get_dynamic_choices(self, slef, dashboard_stats):
        field_name = self.dynamic_criteria_field_name
        if field_name:
            model = apps.get_model(dashboard_stats.model_app_name, dashboard_stats.model_name)
            query = model.objects.all().query
            if self.criteria_dynamic_mapping:
                return dict(self.criteria_dynamic_mapping)
            else:
                if field_name.endswith('__isnull'):
                    return {
                        '': ('', 'All'),
                        'False': (False, 'Non blank'),
                        'True': (True, 'Blank'),
                    }
                field = query.resolve_ref(field_name).field
                if field.__class__ == models.BooleanField:
                    return {
                        '': ('', 'All'),
                        'False': (False, 'False'),
                        'True': (True, 'True'),
                    }
                elif len(field.choices) > 0:
                    return dict(field.choices)
                else:
                    return {i: (i,i) for i in model.objects.values_list(field_name, flat=True)}


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
    default_chart_type = models.CharField(
        max_length=90,
        verbose_name=_("Default chart type"),
        null=False,
        blank=False,
        choices=chart_types,
        default='discreteBarChart',
    )
    default_time_period = models.PositiveIntegerField(
        verbose_name=_("Default period"),
        help_text=_("Number of days"),
        null=False,
        blank=False,
        default=31,
    )
    default_time_scale = models.CharField(
        verbose_name=_("Default time scale"),
        null=False,
        blank=False,
        default='days',
        choices=time_scales,
        max_length=90,
    )
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

    def get_time_series(self, dynamic_criteria, request, time_since, time_until, interval):
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
                if dynamic_key in dynamic_criteria:
                    if dynamic_criteria[dynamic_key] != '':
                        criteria_value = i.get_dynamic_choices(i, self)[dynamic_criteria[dynamic_key]]
                        if isinstance(criteria_value, (list, tuple)):
                            criteria_value = criteria_value[0]
                        kwargs[i.dynamic_criteria_field_name] = criteria_value

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

    def get_multi_time_series(self, request, time_since, time_until, interval):
        try:
            criteria_id = int(request.GET.get('select_box_multiple_series', ''))
            criteria = self.criteria.get(use_as='multiple_series', pk=criteria_id)
        except (DashboardStatsCriteria.DoesNotExist, ValueError):
            criteria = None
        series = {}
        if criteria and criteria.dynamic_criteria_field_name:
            for key, name in criteria.get_dynamic_choices(criteria, self).items():
                if key != '':
                    if isinstance(name, (list, tuple)):
                        name = name[1]
                    series[name] = self.get_time_series({'select_box_dynamic_' + str(criteria.id): key}, request, time_since, time_until, interval)
        else:
            series[''] = self.get_time_series(request.GET, request, time_since, time_until, interval)
        return series

    def get_control_form(self):
        """ Get content of the ajax control form """
        temp = ''
        for i in self.criteria.filter(use_as='chart_filter'):
            dy_map = i.get_dynamic_choices(i, self)
            if dy_map:
                temp += i.criteria_name + ': <select class="chart-input dynamic_criteria_select_box" name="select_box_dynamic_%i" >' % i.id
                for key, name in dy_map.items():
                    if isinstance(name, (list, tuple)):
                        name = name[1]
                    temp += '<option value="%s">%s</option>' % (key, name)
                temp += '</select>'

        temp += '<input type="hidden" class="hidden_graph_key" name="graph_key" value="%s">' % self.graph_key

        multiple_series = self.criteria.filter(use_as='multiple_series')
        if multiple_series.exists():
            temp += 'Divide: <select class="chart-input select_box_multiple_series" name="select_box_multiple_series" >'
            temp += '<option class="chart-input" value="">-------</option>'
            selected_str = 'selected=selected'
            for serie in multiple_series.all():
                temp += '<option class="chart-input" value="%s" %s>%s</option>' % (serie.id, selected_str, serie.criteria_name)
                selected_str = ""
            temp += '</select>'

        temp += 'Scale: <select class="chart-input select_box_interval" name="select_box_interval" >'
        for interval, interval_name in time_scales:
            selected_str = 'selected=selected' if interval == self.default_time_scale else ''
            temp += '<option class="chart-input" value="' + interval + '" ' + selected_str + '>' + interval_name + '</option>'
        temp += '</select>'

        temp += 'Since: <input class="chart-input select_box_date_since" type="date" name="time_since" value="%s">' % \
            (now() - timedelta(days=self.default_time_period)).strftime('%Y-%m-%d')
        temp += 'Until: <input class="chart-input select_box_date_since" type="date" name="time_until" value="%s">' % \
            now().strftime('%Y-%m-%d')

        temp += 'Chart: <select class="chart-input select_box_chart_type" name="select_box_chart_type" >'
        for chart_type_str, chart_type_name in chart_types:
            selected_str = 'selected=selected' if chart_type_str == self.default_chart_type else ''
            temp += '<option class="chart-input" value="' + chart_type_str + '" ' + selected_str + '>' + chart_type_name + '</option>'
        temp += '</select>'

        return mark_safe(force_text(temp))

    def __str__(self):
            return u"%s" % self.graph_key

    @classmethod
    def get_active_graph(cls):
        """Returns active graphs"""
        return DashboardStats.objects.filter(is_visible=1).prefetch_related('criteria')
