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

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
import jsonfield.fields

operation = (
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
        help_text=_("a JSON dictionary of key-value pairs that will be used for the criteria"))
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
                                 verbose_name=_('graph key'),
                                 help_text=_("it needs to be one word unique. ex. auth, mygraph"))
    graph_title = models.CharField(max_length=90, db_index=True,
                                   verbose_name=_('graph title'),
                                   help_text=_("heading title of graph box"))
    model_app_name = models.CharField(max_length=90, verbose_name=_('app name'),
                                      help_text=_("ex. auth / dialer_cdr"))
    model_name = models.CharField(max_length=90, verbose_name=_('model name'),
                                  help_text=_("ex. User"))
    date_field_name = models.CharField(max_length=90, verbose_name=_("date field name"),
                                       help_text=_("ex. date_joined"))
    operation_field_name = models.CharField(max_length=90, verbose_name=_("Operate field name"),
                                      null=True, blank=True,
                                      help_text=_("The field you want to aggregate, ex. amount"))
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

    def __str__(self):
            return u"%s" % self.graph_key
