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
import logging
from collections import OrderedDict
from datetime import date, datetime, timedelta

from cache_utils.decorators import cached

from dateutil.relativedelta import relativedelta

from django.apps import apps
from django.core.exceptions import FieldError, ValidationError
from django.db import models
from django.db.models import ExpressionWrapper, Q
from django.db.models.aggregates import Avg, Count, Max, Min, StdDev, Sum, Variance
from django.db.models.functions import Trunc
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

import jsonfield.fields

from qsstats.utils import get_bounds

logger = logging.getLogger(__name__)

operation = (
    ('Count', 'Count'),
    ('Sum', 'Sum'),
    ('Avg', 'Avgerage'),
    ('AvgCountPerInstance', 'Avgerage count per active model instance'),
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
    criteria_name = models.CharField(
        max_length=90, db_index=True,
        verbose_name=_('criteria name'),
        help_text=_("it needs to be one word unique. Ex. status, yesno"),
    )
    criteria_fix_mapping = jsonfield.fields.JSONField(
        null=True, blank=True,
        verbose_name=_("fixed criteria / value"),
        help_text=_("a JSON dictionary of key-value pairs that will be used for the criteria"),
    )
    dynamic_criteria_field_name = models.CharField(
        max_length=90, blank=True, null=True,
        verbose_name=_("dynamic criteria field name"),
        help_text=_("ex. for call records - disposition"),
    )
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
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "admin_tools_stats"
        db_table = u'dash_stats_criteria'
        verbose_name = _("dashboard stats criteria")
        verbose_name_plural = _("dashboard stats criteria")

    def __str__(self):
        return u"%s" % self.criteria_name


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
    graph_key = models.CharField(
        unique=True, max_length=90,
        verbose_name=_('graph identifier'),
        help_text=_("it needs to be one word unique. ex. auth, mygraph"),
    )
    graph_title = models.CharField(
        max_length=90, db_index=True,
        verbose_name=_('graph title'),
        help_text=_("heading title of graph box"),
    )
    model_app_name = models.CharField(
        max_length=90, verbose_name=_('app name'),
        help_text=_("ex. auth / dialer_cdr"),
    )
    model_name = models.CharField(
        max_length=90, verbose_name=_('model name'),
        help_text=_("ex. User"),
    )
    date_field_name = models.CharField(
        max_length=90, verbose_name=_("date field name"),
        help_text=_("ex. date_joined, invitation__invitation_date"),
    )
    user_field_name = models.CharField(
        max_length=90, verbose_name=_("user field name"),
        null=True, blank=True,
        help_text=_("ex. owner, invitation__owner"),
    )
    operation_field_name = models.CharField(
        max_length=90, verbose_name=_("Operate field name"),
        null=True, blank=True,
        help_text=_("The field you want to aggregate, ex. amount, salaries__total_income"),
    )
    distinct = models.BooleanField(
        default=False,
        null=False,
        blank=True,
        help_text=_(
            "Note: Distinct is supported only for Count, Sum, Avg and 'Avgerage count per active model instance'.<br/>"
            "Django>=3.0 is needed for distinct Sum and Avg."
        ),
    )
    type_operation_field_name = models.CharField(
        max_length=90, verbose_name=_("Choose Type operation"),
        null=True, blank=True, choices=operation,
        help_text=_("choose the type operation what you want to aggregate, ex. Sum"),
    )
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
    y_axis_format = models.CharField(
        max_length=90,
        verbose_name=_("Y axis format"),
        help_text=_(
            "Format of Y axis."
            "<a href='https://github.com/d3/d3-format' target='_blank'>See description of possible values</a>."
        ),
        null=True,
        blank=True,
        default=None,
    )
    criteria = models.ManyToManyField(DashboardStatsCriteria, blank=True, through='CriteriaToStatsM2M')
    is_visible = models.BooleanField(default=True, verbose_name=_('visible'))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "admin_tools_stats"
        db_table = u'dashboard_stats'
        verbose_name = _("dashboard stats")
        verbose_name_plural = _("dashboard stats")

    def get_model(self):
        return apps.get_model(self.model_app_name, self.model_name)

    def get_operation_field(self):
        query = self.get_model().objects.all().query
        return query.resolve_ref(self.operation_field_name).field

    def get_date_field(self):
        query = self.get_model().objects.all().query
        return query.resolve_ref(self.date_field_name).field

    def clean(self, *args, **kwargs):
        errors = {}
        model = None
        try:
            apps.get_app_config(self.model_app_name)
        except LookupError as e:
            errors['model_app_name'] = str(e)

        try:
            model = self.get_model()
        except LookupError as e:
            errors['model_name'] = str(e)

        try:
            if model and self.operation_field_name:
                self.get_operation_field()
        except FieldError as e:
            errors['operation_field_name'] = str(e)

        try:
            if model and self.date_field_name:
                self.get_date_field()
        except FieldError as e:
            errors['date_field_name'] = str(e)

        raise ValidationError(errors)
        return super(DashboardStats, self).clean(*args, **kwargs)

    def get_time_series(self, dynamic_criteria, all_criteria, request, time_since, time_until, interval):
        """ Get the stats time series """
        model_name = apps.get_model(self.model_app_name, self.model_name)
        kwargs = {}
        dynamic_kwargs = []
        if request and not request.user.is_superuser and self.user_field_name:
            kwargs[self.user_field_name] = request.user
        for m2m in all_criteria:
            criteria = m2m.criteria
            # fixed mapping value passed info kwargs
            if criteria.criteria_fix_mapping:
                for key in criteria.criteria_fix_mapping:
                    # value => criteria.criteria_fix_mapping[key]
                    kwargs[key] = criteria.criteria_fix_mapping[key]

            # dynamic mapping value passed info kwargs
            dynamic_key = "select_box_dynamic_%i" % m2m.id
            if dynamic_key in dynamic_criteria:
                if dynamic_criteria[dynamic_key] != '':
                    dynamic_values = dynamic_criteria[dynamic_key]
                    dynamic_field_name = m2m.get_dynamic_criteria_field_name()
                    criteria_key = 'id' if dynamic_field_name == '' else dynamic_field_name
                    if isinstance(dynamic_values, (list, tuple)):
                        single_value = False
                    else:
                        dynamic_values = (dynamic_values,)
                        single_value = True

                    for dynamic_value in dynamic_values:
                        criteria_value = m2m.get_dynamic_choices()[dynamic_value]
                        if isinstance(criteria_value, (list, tuple)):
                            criteria_value = criteria_value[0]
                        else:
                            criteria_value = dynamic_value
                        if single_value:
                            kwargs[criteria_key] = criteria_value
                        else:
                            dynamic_kwargs.append(Q(**{criteria_key: criteria_value}))

        aggregate_dict = {}
        i = 0
        if not dynamic_kwargs:
            dynamic_kwargs = [None]

        for dkwargs in dynamic_kwargs:
            i += 1
            if not self.type_operation_field_name:
                self.type_operation_field_name = 'Count'
            if not self.operation_field_name:
                self.operation_field_name = 'id'

            operation = {
                'AvgCountPerInstance': lambda field_name, distinct, dkwargs: ExpressionWrapper(
                    1.0 *
                    Count(field_name, distinct=distinct, filter=dkwargs) /
                    Count('id', distinct=True, filter=Q(**{field_name + "__isnull": False})),
                    output_field=models.FloatField()
                ),
                'Count': lambda field_name, distinct, dkwargs: Count(field_name, distinct=distinct, filter=dkwargs),
                'Sum': lambda field_name, distinct, dkwargs: Sum(field_name, distinct=distinct, filter=dkwargs),
                'Avg': lambda field_name, distinct, dkwargs: Avg(field_name, distinct=distinct, filter=dkwargs),
                'StdDev': lambda field_name, distinct, dkwargs: StdDev(field_name, filter=dkwargs),
                'Max': lambda field_name, distinct, dkwargs: Max(field_name, filter=dkwargs),
                'Min': lambda field_name, distinct, dkwargs: Min(field_name, filter=dkwargs),
                'Variance': lambda field_name, distinct, dkwargs: Variance(field_name, filter=dkwargs),
            }
            aggregate_dict['agg_%i' % i] = operation[self.type_operation_field_name](self.operation_field_name, self.distinct, dkwargs)

        # TODO: maybe backport values_list support back to django-qsstats-magic and use it again for the query
        time_range = {'%s__range' % self.date_field_name: (time_since, time_until)}
        qs = model_name.objects
        qs = qs.filter(**time_range)
        qs = qs.filter(**kwargs)
        if hasattr(time_since, 'tzinfo') and time_since.tzinfo:
            tzinfo = {'tzinfo': time_since.tzinfo}
        else:
            tzinfo = {}
        qs = qs.annotate(d=Trunc(self.date_field_name, interval, **tzinfo))
        qs = qs.values_list('d')
        qs = qs.order_by('d')
        qs = qs.annotate(**aggregate_dict)
        return qs

    def get_multi_series_criteria(self, request_get):
        try:
            m2m_id = int(request_get.get('select_box_multiple_series', ''))
            criteria = self.criteriatostatsm2m_set.get(use_as='multiple_series', pk=m2m_id)
        except (DashboardStatsCriteria.DoesNotExist, ValueError):
            criteria = None
        return criteria

    def get_multi_time_series(self, configuration, time_since, time_until, interval, request=None):
        configuration = configuration.copy()
        series = {}
        all_criteria = self.criteriatostatsm2m_set.all()  # Outside of get_time_series just for performance reasons
        m2m = self.get_multi_series_criteria(configuration)
        if m2m and m2m.criteria.dynamic_criteria_field_name:
            choices = m2m.get_dynamic_choices()

            serie_map = {}
            names = []
            values = []
            for key, name in choices.items():
                if key != '':
                    if isinstance(name, (list, tuple)):
                        name = name[1]
                    names.append(name)
                    values.append(key)
            configuration['select_box_dynamic_' + str(m2m.id)] = values
            serie_map = self.get_time_series(configuration, all_criteria, request, time_since, time_until, interval)
            for tv in serie_map:
                time = tv[0]
                if time not in series:
                    series[time] = OrderedDict()
                i = 0
                for name in names:
                    i += 1
                    series[time][name] = tv[i]
        else:
            serie = self.get_time_series(configuration, all_criteria, request, time_since, time_until, interval)
            for time, value in serie:
                if type(time) == date:
                    time = datetime.combine(time, datetime.min.time())
                series[time] = {'': value}
            names = {'': ''}

        # fill with zeros where the records are missing
        interval_s = interval.rstrip('s')
        start, _ = get_bounds(time_since, interval_s)
        _, end = get_bounds(time_until, interval_s)

        time = start
        while time < end:
            if time not in series:
                series[time] = OrderedDict()
            for key in names:
                if key not in series[time]:
                    series[time][key] = 0
            time = time + relativedelta(**{interval: 1})
        return series

    def get_control_form(self):
        """ Get content of the ajax control form """
        temp = ''
        for i in self.criteriatostatsm2m_set.filter(use_as='chart_filter').order_by('order'):
            dy_map = i.get_dynamic_choices()
            if dy_map:
                temp += i.criteria.criteria_name + ': <select class="chart-input dynamic_criteria_select_box" name="select_box_dynamic_%i" >' % i.id
                temp += '<option value="">-------</option>'
                for key, name in dy_map.items():
                    if isinstance(name, (list, tuple)):
                        name = name[1]
                    temp += '<option value="%s">%s</option>' % (key, name)
                temp += '</select>'

        temp += '<input type="hidden" class="hidden_graph_key" name="graph_key" value="%s">' % self.graph_key

        multiple_series = self.criteriatostatsm2m_set.filter(use_as='multiple_series')
        if multiple_series.exists():
            temp += 'Divide: <select class="chart-input select_box_multiple_series" name="select_box_multiple_series" >'
            temp += '<option class="chart-input" value="">-------</option>'
            selected_str = 'selected=selected'
            for serie in multiple_series.order_by('order').all():
                temp += '<option class="chart-input" value="%s" %s>%s</option>' % (serie.id, selected_str, serie.criteria.criteria_name)
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


class CriteriaToStatsM2M(models.Model):
    class Meta:
        ordering = ('order',)

    criteria = models.ForeignKey(
        DashboardStatsCriteria,
        on_delete=models.CASCADE,
    )
    stats = models.ForeignKey(
        DashboardStats,
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True,
    )
    prefix = models.CharField(
        max_length=255,
        verbose_name=_('criteria field prefix'),
        default="",
        help_text=_("prefix, that will be added befor all lookup paths of criteria"),
        blank=True,
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

    def get_dynamic_criteria_field_name(self):
        if self.prefix:
            return self.prefix + self.criteria.dynamic_criteria_field_name
        return self.criteria.dynamic_criteria_field_name

    def get_dynamic_field(self, model):
        field_name = self.get_dynamic_criteria_field_name()
        query = model.objects.all().query
        return query.resolve_ref(field_name).field

    # The slef argument is here just because of this bug: https://github.com/infoscout/django-cache-utils/issues/19
    @cached(60 * 5)
    def _get_dynamic_choices(self, slef):
        model = self.stats.get_model()
        field_name = self.get_dynamic_criteria_field_name()
        if self.criteria.criteria_dynamic_mapping:
            return dict(self.criteria.criteria_dynamic_mapping)
        if field_name:
            if field_name.endswith('__isnull'):
                return OrderedDict((
                    ('', ('', 'All')),
                    ('True', (True, 'Blank')),
                    ('False', (False, 'Non blank')),
                ))
            field = self.get_dynamic_field(model)
            if field.__class__ == models.BooleanField:
                return OrderedDict((
                    ('', ('', 'All')),
                    ('True', (True, 'True')),
                    ('False', (False, 'False')),
                ))
            else:
                choices = OrderedDict()
                fchoices = dict(field.choices or [])
                choices.update(
                    (
                        (i, (i, fchoices[i] if i in fchoices else i))
                        for i in
                        model.objects.values_list(field_name, flat=True).distinct().order_by(field_name)
                    ),
                )
                return choices

    def get_dynamic_choices(self):
        choices = self._get_dynamic_choices(self)
        return choices


@receiver(post_save, sender=DashboardStatsCriteria)
def clear_caches_criteria(sender, instance, **kwargs):
    for m2m in instance.criteriatostatsm2m_set.all():
        m2m._get_dynamic_choices.invalidate(m2m)


@receiver(post_save, sender=DashboardStats)
def clear_caches_stats(sender, instance, **kwargs):
    for m2m in instance.criteriatostatsm2m_set.all():
        m2m._get_dynamic_choices.invalidate(m2m)


@receiver(post_save, sender=CriteriaToStatsM2M)
def clear_caches_stats_m2m(sender, instance, **kwargs):
    instance._get_dynamic_choices.invalidate(instance)
