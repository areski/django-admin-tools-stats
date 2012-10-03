from django.db import models
from django.utils.translation import ugettext_lazy as _
import jsonfield.fields


class DashboardStatsCriteria(models.Model):
    """To configure criteria for dashboard graphs

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
                    verbose_name=_('Criteria Name'),
                    help_text=_("It needs to be one word unique. Ex. status, yesno"))
    criteria_fix_mapping = jsonfield.fields.JSONField(null=True, blank=True,
                           verbose_name=_("Fixed Criteria / Value"),
                           help_text=_(u'A JSON Dictionary of key-value pairs that will be used for the criteria'))
    dynamic_criteria_field_name = models.CharField(max_length=90, blank=True, null=True,
                                  verbose_name=_("Dynamic Criteria Field Name"),
                                  help_text=_("Ex. for call records - disposition"))
    criteria_dynamic_mapping = jsonfield.fields.JSONField(null=True, blank=True,
                               verbose_name=_("Dynamic Criteria / Value"),
                               help_text=_(u'A JSON Dictionary of key-value pairs that will be used for the criteria'))
    created_date = models.DateTimeField(auto_now_add=True,
                                        verbose_name=_('Date'))
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'dash_stats_criteria'
        verbose_name = _("Dashboard Stats Criteria")
        verbose_name_plural = _("Dashboard Stats Criteria")

    def __unicode__(self):
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
    graph_key = models.CharField(max_length=90, db_index=True,
                                 verbose_name=_('Graph Key'),
                                 help_text=_("It needs to be one word unique. Ex. auth, mygraph"))
    graph_title = models.CharField(max_length=90, db_index=True,
                                   verbose_name=_('Graph Title'),
                                   help_text=_("Heading title of graph box"))
    model_app_name = models.CharField(max_length=90, verbose_name=_('App Name'),
                                      help_text=_("Ex. auth / dialer_cdr"))
    model_name = models.CharField(max_length=90, verbose_name=_('Model Name'),
                                  help_text=_("Ex. User"))
    date_field_name = models.CharField(max_length=90, verbose_name=_("Date Field Name"),
                                       help_text=_("Ex. date_joined"))
    criteria = models.ManyToManyField(DashboardStatsCriteria, blank=True, null=True)
    is_visible = models.BooleanField(default=True, verbose_name=_('Visible'))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Date'))
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = u'dashboard_stats'
        verbose_name = _("Dashboard Stats")
        verbose_name_plural = _("Dashboard Stats")

    def __unicode__(self):
            return u"%s" % self.graph_key
