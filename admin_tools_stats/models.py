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
import datetime
import logging
from collections import OrderedDict

from cache_utils.decorators import cached
from dateutil.relativedelta import MO, relativedelta
from dateutil.rrule import DAILY, HOURLY, MONTHLY, WEEKLY, YEARLY, rrule
from django.apps import apps
from django.conf import settings
from django.core.exceptions import FieldError, ValidationError
from django.db import models
from django.db.models import ExpressionWrapper, Q
from django.db.models.aggregates import (Avg, Count, Max, Min, StdDev, Sum,
                                         Variance)
from django.db.models.fields import DateField
from django.db.models.functions import Trunc
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField

try:
    if getattr(settings, 'ADMIN_CHARTS_USE_JSONFIELD', True):
        from django.db.models import JSONField
    else:
        from jsonfield.fields import JSONField
except ImportError:
    from jsonfield.fields import JSONField

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
    ('quarters', 'Quarters'),
    ('years', 'Years'),
)
rrule_freqs = {
    'years': {'freq': YEARLY},
    'quarters': {'freq': MONTHLY, 'interval': 3},
    'months': {'freq': MONTHLY},
    'weeks': {'freq': WEEKLY},
    'days': {'freq': DAILY},
    'hours': {'freq': HOURLY},
}


def truncate(dt, interval):
    ''' Returns interval bounds the datetime is in. '''

    day = datetime.datetime(dt.year, dt.month, dt.day, tzinfo=dt.tzinfo)

    if interval == 'hours':
        return datetime.datetime(dt.year, dt.month, dt.day, dt.hour, tzinfo=dt.tzinfo)
    elif interval == 'days':
        return day
    elif interval == 'weeks':
        return day - relativedelta(weekday=MO(-1))
    elif interval == 'months':
        return datetime.datetime(dt.year, dt.month, 1, tzinfo=dt.tzinfo)
    elif interval == 'quarters':
        qmonth = dt.month - (dt.month - 1) % 3
        return datetime.datetime(dt.year, qmonth, 1, tzinfo=dt.tzinfo)
    elif interval == 'years':
        return datetime.datetime(dt.year, 1, 1, tzinfo=dt.tzinfo)


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
    criteria_fix_mapping = JSONField(
        null=True, blank=True,
        verbose_name=_("fixed criteria / value"),
        help_text=_("a JSON dictionary of key-value pairs that will be used for the criteria"),
    )
    dynamic_criteria_field_name = models.CharField(
        max_length=90, blank=True, null=True,
        verbose_name=_("dynamic criteria field name"),
        help_text=_("ex. for call records - disposition"),
    )
    criteria_dynamic_mapping = JSONField(
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

    def criteria_dynamic_mapping_preview(self):
        if self.criteria_dynamic_mapping:
            return str(self.criteria_dynamic_mapping)[0:100] + ("..." if len(str(self.criteria_dynamic_mapping)) > 100 else "")
        return ""

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
        help_text=_("ex. <i>auth</i>, <i>dialer_cdr</i>"),
    )
    model_name = models.CharField(
        max_length=90, verbose_name=_('model name'),
        help_text=_("ex. <i>User</i>"),
    )
    date_field_name = models.CharField(
        max_length=90, verbose_name=_("date field name"),
        help_text=_("ex. <i>date_joined</i>, <i>invitation__invitation_date</i>"),
    )
    user_field_name = models.CharField(
        max_length=90, verbose_name=_("user field name"),
        null=True, blank=True,
        help_text=_(
            "User field that will limit chart data only for currently logged user (if not superuser)<br/>"
            "ex. owner, <i>invitation__owner</i>",
        ),
    )
    show_to_users = models.BooleanField(
        verbose_name=_("show to ordinary users"),
        null=False, blank=False,
        default=False,
        help_text=_("Be carefull and test if it still doesn't expose sensitive data"),
    )
    operation_field_name = models.CharField(
        max_length=90, verbose_name=_("Operate field name"),
        null=True, blank=True,
        help_text=_(
            "The field you want to aggregate, ex. <i>amount</i>, <i>salaries__total_income</i>.<br/>"
            "Can contain multiple fields divided by comma.",
        ),
    )
    distinct = models.BooleanField(
        default=False,
        null=False,
        blank=True,
        help_text=_(
            "Note: Distinct is supported only for <i>Count</i>, <i>Sum</i>, "
            "<i>Avg</i> and <i>'Avgerage count per active model instance'</i>.<br/>"
            "Django>=3.0 is needed for distinct <i>Sum</i> and <i>Avg</i>.",
        ),
    )
    type_operation_field_name = models.CharField(
        max_length=90, verbose_name=_("Choose Type operation"),
        null=True, blank=True, choices=operation,
        help_text=_("Choose the type operation what you want to aggregate."),
    )
    allowed_type_operation_field_name = MultiSelectField(
        max_length=1000, verbose_name=_("Choose Type operation"),
        null=True, blank=True, choices=operation,
        help_text=_("More than one selected field will display chooser on the chart."),
    )
    default_chart_type = models.CharField(
        max_length=90,
        verbose_name=_("Default chart type"),
        null=False,
        blank=False,
        choices=chart_types,
        default='discreteBarChart',
    )
    allowed_chart_types = MultiSelectField(
        max_length=1000,
        verbose_name=_("Allowed chart types"),
        null=True,
        blank=True,
        choices=chart_types,
        default=list(zip(*chart_types))[0],
        help_text=_("More than one selected field will display chooser on the chart."),
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
    allowed_time_scales = MultiSelectField(
        max_length=1000,
        verbose_name=_("Allowed time scales"),
        choices=time_scales,
        default=list(zip(*time_scales))[0],
        help_text=_("More than one selected field will display chooser on the chart."),
    )
    y_axis_format = models.CharField(
        max_length=90,
        verbose_name=_("Y axis format"),
        help_text=_(
            "Format of Y axis."
            "<a href='https://github.com/d3/d3-format' target='_blank'>See description of possible values</a>.",
        ),
        null=True,
        blank=True,
        default=None,
    )
    criteria = models.ManyToManyField(DashboardStatsCriteria, blank=True, through='CriteriaToStatsM2M')
    default_multiseries_criteria = models.ForeignKey(
        'CriteriaToStatsM2M',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        # limit_choices_to={'stats__id': Value('id')},  #TODO: solve this issue and enable: https://code.djangoproject.com/ticket/25306
        related_name='default_choices_stats',
    )
    is_visible = models.BooleanField(default=True, verbose_name=_('visible'))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "admin_tools_stats"
        db_table = u'dashboard_stats'
        verbose_name = _("dashboard stats")
        verbose_name_plural = _("dashboard stats")

    def allowed_type_operation_field_name_choices(self):
        return (op for op in operation if op[0] in self.allowed_type_operation_field_name)

    def allowed_time_scales_choices(self):
        return (ts for ts in time_scales if ts[0] in self.allowed_time_scales)

    def allowed_chart_types_choices(self):
        return (cht for cht in chart_types if cht[0] in self.allowed_chart_types)

    def get_model(self):
        return apps.get_model(self.model_app_name, self.model_name)

    def get_operation_field(self, operation):
        query = self.get_model().objects.all().query
        return query.resolve_ref(operation).field

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
            for operation in self.get_operations_list():
                if model and operation:
                    self.get_operation_field(operation)
        except FieldError as e:
            errors['operation_field_name'] = str(e)

        try:
            if model and self.date_field_name:
                self.get_date_field()
        except FieldError as e:
            errors['date_field_name'] = str(e)

        raise ValidationError(errors)
        return super(DashboardStats, self).clean(*args, **kwargs)

    def get_operations_list(self):
        if self.operation_field_name:
            return self.operation_field_name.split(',')
        return []

    def get_operation(self, operation_choice, operation_field_choice, dkwargs=None):
        if not operation_choice:
            operation_choice = self.type_operation_field_name or 'Count'
        if not operation_field_choice:
            operations = self.get_operations_list()
            operation_field_choice = operations[0] if operations else 'id'
        if not operation_field_choice:
            self.operation_field_name = 'id'

        operations = {
            'AvgCountPerInstance': lambda field_name, distinct, dkwargs: ExpressionWrapper(
                1.0 *
                Count(field_name, distinct=distinct, filter=dkwargs) /
                Count('id', distinct=True, filter=Q(**{field_name + "__isnull": False})),
                output_field=models.FloatField(),
            ),
            'Count': lambda field_name, distinct, dkwargs: Count(field_name, distinct=distinct, filter=dkwargs),
            'Sum': lambda field_name, distinct, dkwargs: Sum(field_name, distinct=distinct, filter=dkwargs),
            'Avg': lambda field_name, distinct, dkwargs: Avg(field_name, distinct=distinct, filter=dkwargs),
            'StdDev': lambda field_name, distinct, dkwargs: StdDev(field_name, filter=dkwargs),
            'Max': lambda field_name, distinct, dkwargs: Max(field_name, filter=dkwargs),
            'Min': lambda field_name, distinct, dkwargs: Min(field_name, filter=dkwargs),
            'Variance': lambda field_name, distinct, dkwargs: Variance(field_name, filter=dkwargs),
        }
        return operations[operation_choice](operation_field_choice, self.distinct, dkwargs)

    def get_time_series(self, dynamic_criteria, all_criteria, user, time_since, time_until, operation_choice, operation_field_choice, interval):
        """ Get the stats time series """
        model_name = apps.get_model(self.model_app_name, self.model_name)
        kwargs = {}
        dynamic_kwargs = []
        if not user.has_perm('admin_tools_stats.view_dashboardstats') and self.user_field_name:
            kwargs[self.user_field_name] = user
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
                        try:
                            criteria_value = m2m.get_dynamic_choices(
                                time_since, time_until, operation_choice, operation_field_choice, user,
                            )[dynamic_value]
                        except KeyError:
                            criteria_value = 0
                        if isinstance(criteria_value, (list, tuple)):
                            criteria_value = criteria_value[0]
                        else:
                            criteria_value = dynamic_value
                        criteria_key_string = criteria_key + ("__in" if isinstance(criteria_value, list) else "")
                        if single_value:
                            kwargs[criteria_key_string] = criteria_value
                        else:
                            dynamic_kwargs.append(Q(**{criteria_key_string: criteria_value}))

        aggregate_dict = {}
        i = 0
        if not dynamic_kwargs:
            dynamic_kwargs = [None]

        operations = self.get_operations_list()
        if operations and len(operations) > 1 and dynamic_criteria['select_box_operation_field'] == '':
            for operation in operations:
                i += 1
                aggregate_dict['agg_%i' % i] = self.get_operation(operation_choice, operation)
        else:
            for dkwargs in dynamic_kwargs:
                i += 1
                aggregate_dict['agg_%i' % i] = self.get_operation(operation_choice, operation_field_choice, dkwargs)

        # TODO: maybe backport values_list support back to django-qsstats-magic and use it again for the query
        time_range = {'%s__range' % self.date_field_name: (time_since, time_until)}
        qs = model_name.objects
        qs = qs.filter(**time_range)
        qs = qs.filter(**kwargs)
        kind = interval[:-1]
        qs = qs.annotate(d=Trunc(self.date_field_name, kind))
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

    def get_multi_time_series(self, configuration, time_since, time_until, interval, operation_choice, operation_field_choice, user):
        current_tz = timezone.get_current_timezone()
        time_since_tz = time_since.astimezone(current_tz)
        time_until_tz = time_until.astimezone(current_tz).replace(hour=23, minute=59)

        configuration = configuration.copy()
        series = {}
        all_criteria = self.criteriatostatsm2m_set.all()  # Outside of get_time_series just for performance reasons
        m2m = self.get_multi_series_criteria(configuration)

        values = []
        names = []
        operations = self.get_operations_list()
        if m2m and m2m.criteria.dynamic_criteria_field_name:
            choices = m2m.get_dynamic_choices(time_since_tz, time_until_tz, operation_choice, operation_field_choice, user)
            for key, name in choices.items():
                if key != '':
                    if isinstance(name, (list, tuple)):
                        name = name[1]
                    names.append(name)
                    values.append(key)
            configuration['select_box_dynamic_' + str(m2m.id)] = values
        elif len(operations) > 1 and configuration['select_box_operation_field'] == '':
            names = operations
        else:
            names = ['']

        serie_map = {}
        serie_map = self.get_time_series(
            configuration, all_criteria, user, time_since_tz, time_until_tz, operation_choice, operation_field_choice, interval,
        )
        for tv in serie_map:
            time = tv[0]
            if time not in series:
                series[time] = {}
            i = 0
            for name in names:
                i += 1
                series[time][name] = tv[i]

        # fill with zeros where the records are missing
        start = truncate(time_since, interval)

        dates = list(rrule(**rrule_freqs[interval], dtstart=start, until=time_until))
        for time in dates:
            if self.get_date_field().__class__ == DateField:
                time = time.date()
            elif settings.USE_TZ:
                time = time.astimezone(current_tz)

            if time not in series:
                series[time] = {}
            for key in names:
                if key not in series[time]:
                    series[time][key] = 0
        return series

    def get_control_form_raw(self, user=None):
        from .forms import ChartSettingsForm
        return ChartSettingsForm(self, user, auto_id=False)

    def get_control_form(self, user=None):
        """ Get content of the ajax control form """
        return self.get_control_form_raw(user).as_p()

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
    default_option = models.CharField(
        max_length=255,
        verbose_name=_('Default filter criteria option'),
        help_text=_('Works only with Chart filter criteri'),
        default="",
        blank=True,
    )
    choices_based_on_time_range = models.BooleanField(
        verbose_name=_('Choices are dependend on chart time range'),
        help_text=_('Choices are not cached if this is set to true'),
        default=False,
    )
    count_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
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
    def _get_dynamic_choices(
            self, slef, time_since=None, time_until=None, count_limit=None,
            operation_choice=None, operation_field_choice=None, user=None,
    ):
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
                date_filters = {}
                current_tz = timezone.get_current_timezone()
                if time_since is not None:
                    if time_since.tzinfo is None or time_since.tzinfo.utcoffset(time_since) is None:
                        time_since = current_tz.localize(time_since)
                    date_filters['%s__gte' % self.stats.date_field_name] = time_since
                if time_until is not None:
                    if time_until.tzinfo is None or time_until.tzinfo.utcoffset(time_until) is None:
                        time_until = current_tz.localize(time_until).replace(hour=23, minute=59)
                    end_time = time_until
                    date_filters['%s__lte' % self.stats.date_field_name] = end_time
                choices_queryset = model.objects.filter(
                        **date_filters,
                    )
                if user and not user.has_perm('admin_tools_stats.view_dashboardstats'):
                    if not self.stats.user_field_name:
                        raise Exception("User field must be defined to enable charts for non-superusers")
                    choices_queryset = choices_queryset.filter(**{self.stats.user_field_name: user})
                choices_queryset = choices_queryset.values_list(
                        field_name,
                        flat=True,
                    ).distinct()
                if count_limit:
                    choices_queryset = choices_queryset.annotate(
                        f_count=self.stats.get_operation(operation_choice, operation_field_choice),
                    ).order_by(
                        '-f_count',
                    )
                    choices_list = list(choices_queryset)
                    other_choices_queryset = choices_list[count_limit:]
                    choices_queryset = choices_list[:count_limit]
                else:
                    choices_queryset = choices_queryset.order_by(field_name)
                choices.update(
                    (
                        (i, (i, fchoices[i] if i in fchoices else i))
                        for i in choices_queryset
                    ),
                )
                if count_limit:
                    choices.update(
                        [('other', ([i for i in other_choices_queryset], 'other'))],
                    )
                    choices.move_to_end('other', last=False)
                return choices

    def __str__(self):
        return f"{self.stats.graph_title} - {self.criteria.criteria_name}"

    def get_dynamic_choices(self, time_since=None, time_until=None, operation_choice=None, operation_field_choice=None, user=None):
        if not self.choices_based_on_time_range:
            time_since = None
            time_until = None
        choices = self._get_dynamic_choices(self, time_since, time_until, self.count_limit, operation_choice, operation_field_choice, user)
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
