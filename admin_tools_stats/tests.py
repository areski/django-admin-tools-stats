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
from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from model_mommy import mommy

from admin_tools_stats.models import DashboardStatsCriteria
from admin_tools_stats.utils import BaseAuthenticatedClient, assertContainsAny


class AdminToolsStatsAdminInterfaceTestCase(BaseAuthenticatedClient):
    """
    Test cases for django-admin-tools-stats Admin Interface
    """

    def test_admin_tools_stats_dashboardstats(self):
        """Test function to check dashboardstats admin pages"""
        response = self.client.get('/admin/admin_tools_stats/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/admin_tools_stats/dashboardstats/')
        self.assertEqual(response.status_code, 200)

    def test_admin_tools_stats_dashboardstatscriteria(self):
        """Test function to check dashboardstatscriteria admin pages"""
        response = \
            self.client.get('/admin/admin_tools_stats/dashboardstatscriteria/')
        self.assertEqual(response.status_code, 200)


class AdminToolsStatsAdminCharts(BaseAuthenticatedClient):
    fixtures = ['test_data', 'auth_user']

    def test_admin_dashboard_page(self):
        """Test function to check dashboardstatscriteria admin pages"""
        response = self.client.get('/admin/')
        self.assertContains(
            response,
            '<h2>User graph</h2>',
            html=True,
        )
        self.assertContains(
            response,
            '<h2>User logged in graph</h2>',
            html=True,
        )
        self.assertContains(
            response,
            '<svg style="width:100%;height:300px;"></svg>',
            html=True,
        )
        self.assertContains(
            response,
            '<option value="true">Active</option>',
            html=True,
        )
        self.assertContains(
            response,
            '<option value="false">Inactive</option>',
            html=True,
        )

    def test_admin_dashboard_page_post(self):
        """Test function to check dashboardstatscriteria admin pages"""
        response = self.client.post('/admin/', {'select_box_user_graph': 'true'})
        self.assertContains(
            response,
            '<input type="hidden" class="hidden_graph_key" name="graph_key" value="user_graph">',
            html=True,
        )
        self.assertContains(
            response,
            '<option value="true">Active</option>',
            html=True,
        )


class ModelTests(TestCase):
    maxDiff = None

    def setUp(self):
        self.stats = mommy.make(
            'DashboardStats',
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
        )

    def test_clean_error_model_app_app_name(self):
        stats = mommy.make('DashboardStats', model_name="User1", model_app_name="auth1", graph_key="error_graph")
        with self.assertRaisesRegexp(ValidationError, "model_name.*No installed app with label"):
            stats.clean()

    def test_clean_error_model_name(self):
        stats = mommy.make('DashboardStats', model_name="User1", model_app_name="auth", graph_key="error_graph")
        with self.assertRaisesRegexp(ValidationError, "model_name.*App 'auth' doesn't have a 'User1' model."):
            stats.clean()

    def test_clean_error_operation_field(self):
        stats = mommy.make('DashboardStats', model_name="User", model_app_name="auth", graph_key="error_graph", operation_field_name='asdf')
        with self.assertRaisesRegexp(ValidationError, "operation_field_name.*Cannot resolve keyword 'asdf' into field. Choices are:"):
            stats.clean()

    def test_clean_error_date_field(self):
        stats = mommy.make('DashboardStats', model_name="User", model_app_name="auth", graph_key="error_graph", date_field_name='asdf')
        with self.assertRaisesRegexp(ValidationError, "date_field_name.*Cannot resolve keyword 'asdf' into field. Choices are:"):
            stats.clean()

    @override_settings(USE_TZ=False)
    def test_get_multi_series(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        mommy.make('User', date_joined=datetime.date(2010, 10, 10))
        time_since = datetime.date(2010, 10, 8)
        time_until = datetime.date(2010, 10, 12)

        interval = "days"
        serie = self.stats.get_multi_time_series({}, time_since, time_until, interval)
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 9, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 10, 0, 0): {'': 1},
            datetime.datetime(2010, 10, 11, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 12, 0, 0): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=False)
    def test_get_multi_series_distinct_count(self):
        """Test function to check DashboardStats.get_multi_time_series() with distinct count."""
        stats = mommy.make(
            'DashboardStats',
            model_name="User",
            date_field_name='date_joined',
            model_app_name="auth",
            type_operation_field_name="Count",
            distinct=True,
            operation_field_name='first_name',
        )
        mommy.make('User', date_joined=datetime.date(2010, 10, 10), first_name="Foo")
        mommy.make('User', date_joined=datetime.date(2010, 10, 10), first_name="Foo")
        mommy.make('User', date_joined=datetime.date(2010, 10, 10), first_name="Bar")
        time_since = datetime.date(2010, 10, 8)
        time_until = datetime.date(2010, 10, 12)

        interval = "days"
        serie = stats.get_multi_time_series({}, time_since, time_until, interval)
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 9, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 10, 0, 0): {'': 2},
            datetime.datetime(2010, 10, 11, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 12, 0, 0): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=False)
    def test_get_multi_series_distinct_functions(self):
        """Test function to check DashboardStats.get_multi_time_series() with various functions."""
        for func, result in (
                ("Sum", 15),
                ("Avg", 5),
                ("Min", 1),
                ("Max", 12),
                ("StdDev", 4.96655480858378),
                ("Variance", 24.666666666666668),
                ("AvgCountPerInstance", 1),
        ):
            stats = mommy.make(
                'DashboardStats',
                model_name="TestKid",
                date_field_name='birthday',
                model_app_name="demoproject",
                type_operation_field_name=func,
                operation_field_name='age',
            )
            mommy.make('TestKid', birthday=datetime.date(2010, 10, 10), age=12)
            mommy.make('TestKid', birthday=datetime.date(2010, 10, 10), age=1)
            mommy.make('TestKid', birthday=datetime.date(2010, 10, 10), age=2)
            time_since = datetime.date(2010, 10, 9)
            time_until = datetime.date(2010, 10, 10)

            interval = "days"
            serie = stats.get_multi_time_series({}, time_since, time_until, interval)
            self.assertEqual(serie[datetime.datetime(2010, 10, 10, 0, 0)][''], result, "Bad value for function %s" % func)

    @override_settings(USE_TZ=False)
    def test_get_multi_series_dynamic_field_name(self):
        """Test function to check DashboardStats.get_multi_time_series() with dynamic criteria mapping"""
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "": [None, "All"],
                "false": [False, "Inactive"],
                "true": [True, "Active"],
            },
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series')
        mommy.make('User', date_joined=datetime.date(2010, 10, 12), is_active=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 13), is_active=False)
        time_since = datetime.date(2010, 10, 10)
        time_until = datetime.date(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Active', 1), ('Inactive', 0))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Active', 0), ('Inactive', 1))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=False)
    def test_get_multi_series_dynamic_field_name_old_format(self):
        """
        Test function to check DashboardStats.get_multi_time_series() with dynamic criteria mapping
        the criteria is given in old format
        """
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "False": "Inactive",
                "True": "Active",
            },
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series')
        mommy.make('User', date_joined=datetime.date(2010, 10, 12), is_active=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 13), is_active=False)
        time_since = datetime.date(2010, 10, 10)
        time_until = datetime.date(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Active', 1), ('Inactive', 0))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Active', 0), ('Inactive', 1))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=False)
    def test_get_multi_series_criteria_without_dynamic_mapping(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        DashboardStatsCriteria is set, but without dynamic mapping, so the values are autogenerated.
        """
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series')
        mommy.make('User', date_joined=datetime.date(2010, 10, 12), is_active=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 13), is_active=False)
        time_since = datetime.date(2010, 10, 10)
        time_until = datetime.date(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('True', 0), ('False', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('True', 0), ('False', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('True', 1), ('False', 0))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('True', 0), ('False', 1))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('True', 0), ('False', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=False)
    def test_get_multi_series_criteria_without_dynamic_mapping_choices(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        DashboardStatsCriteria is set, but without dynamic mapping, so the values are autogenerated on CharField.
        """
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series')
        mommy.make('User', date_joined=datetime.date(2010, 10, 12), last_name="Foo")
        mommy.make('User', date_joined=datetime.date(2010, 10, 13), last_name="Bar")
        mommy.make('User', date_joined=datetime.date(2010, 10, 14))
        time_since = datetime.date(2010, 10, 10)
        time_until = datetime.date(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Bar', 0), ('Foo', 1))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Bar', 1), ('Foo', 0))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=False)
    def test_get_multi_series_criteria_combine(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Try to combine multiple_series filter with chart_filter.
        """
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        criteria_active = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series')
        m2m_active = mommy.make('CriteriaToStatsM2M', criteria=criteria_active, stats=self.stats, use_as='chart_filter')
        mommy.make('User', date_joined=datetime.date(2010, 10, 12), last_name="Foo", is_active=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 13), last_name="Bar", is_active=False)
        time_since = datetime.date(2010, 10, 10)
        time_until = datetime.date(2010, 10, 14)

        interval = "days"
        arguments = {'select_box_multiple_series': m2m.id, 'select_box_dynamic_%s' % m2m_active.id: 'True'}
        serie = self.stats.get_multi_time_series(arguments, time_since, time_until, interval)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Bar', 0), ('Foo', 1))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=False)
    def test_get_multi_series_fixed_criteria(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Try to combine multiple_series filter with chart_filter.
        """
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        criteria_active = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="active",
            criteria_fix_mapping={"is_active": True},
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series')
        mommy.make('CriteriaToStatsM2M', criteria=criteria_active, stats=self.stats, use_as='chart_filter')
        mommy.make('User', date_joined=datetime.date(2010, 10, 12), last_name="Foo", is_active=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 13), last_name="Bar", is_active=False)
        time_since = datetime.date(2010, 10, 10)
        time_until = datetime.date(2010, 10, 14)

        interval = "days"
        arguments = {'select_box_multiple_series': m2m.id}
        serie = self.stats.get_multi_time_series(arguments, time_since, time_until, interval)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Bar', 0), ('Foo', 1))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
        }
        self.assertDictEqual(serie, testing_data)


class ViewsTests(BaseAuthenticatedClient):
    def setUp(self):
        self.stats = mommy.make(
            'DashboardStats',
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
        )
        super().setUp()

    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_get_multi_series(self):
        """Test function view rendering multi series"""
        mommy.make('User', date_joined=datetime.datetime(2010, 10, 10, tzinfo=datetime.timezone.utc))
        url = reverse('chart-data', kwargs={'graph_key': 'user_graph'})
        url += "?time_since=2010-10-08&time_until=2010-10-12&select_box_interval=days&select_box_chart_type=discreteBarChart"
        response = self.client.get(url)
        assertContainsAny(self, response, ('{"x": 1286668800000, "y": 1}', '{"y": 1, "x": 1286668800000}'))

    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_get_multi_series_dynamic_criteria(self):
        """Test function view rendering multi series with dynamic criteria"""
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "": [None, "All"],
                "false": [True, "Inactive"],
                "true": [False, "Active"],
            },
        )
        mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series', id=5)
        mommy.make('User', date_joined=datetime.datetime(2010, 10, 10, tzinfo=datetime.timezone.utc))
        url = reverse('chart-data', kwargs={'graph_key': 'user_graph'})
        url += "?time_since=2010-10-08"
        url += "&time_until=2010-10-12"
        url += "&select_box_interval=days"
        url += "&select_box_chart_type=discreteBarChart"
        url += "&select_box_multiple_series=5"
        url += "&debug=True"
        response = self.client.get(url)
        self.assertContains(response, ('"key": "Inactive"'))
        self.assertContains(response, ('"key": "Active"'))


class AdminToolsStatsModel(TestCase):
    """
    Test DashboardStatsCriteria, DashboardStats models
    """
    def setUp(self):
        # DashboardStatsCriteria model
        self.dashboard_stats_criteria = DashboardStatsCriteria(
            criteria_name="call_type",
            criteria_fix_mapping='',
            dynamic_criteria_field_name='disposition',
            criteria_dynamic_mapping={
                "INVALIDARGS": "INVALIDARGS",
                "BUSY": "BUSY",
                "TORTURE": "TORTURE",
                "ANSWER": "ANSWER",
                "DONTCALL": "DONTCALL",
                "FORBIDDEN": "FORBIDDEN",
                "NOROUTE": "NOROUTE",
                "CHANUNAVAIL": "CHANUNAVAIL",
                "NOANSWER": "NOANSWER",
                "CONGESTION": "CONGESTION",
                "CANCEL": "CANCEL",
            },
        )
        self.dashboard_stats_criteria.save()
        self.assertEqual(self.dashboard_stats_criteria.__str__(), 'call_type')

        # DashboardStats model
        self.dashboard_stats = mommy.make(
            'DashboardStats',
            graph_key='user_graph_test',
            graph_title='User graph',
            model_app_name='auth',
            model_name='User',
            date_field_name='date_joined',
            is_visible=1,
        )
        mommy.make('CriteriaToStatsM2M', criteria=self.dashboard_stats_criteria, stats=self.dashboard_stats, use_as='multiple_series')
        with self.assertRaises(ValidationError) as e:
            self.dashboard_stats.clean()
        self.assertEqual(e.exception.message_dict, {})
        self.assertEqual(self.dashboard_stats.__str__(), 'user_graph_test')

    def test_dashboard_criteria(self):
        self.assertEqual(self.dashboard_stats_criteria.criteria_name, "call_type")
        self.assertEqual(self.dashboard_stats.graph_key, 'user_graph_test')

    def teardown(self):
        self.dashboard_stats_criteria.delete()
        self.dashboard_stats.delete()
