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

from admin_tools_stats.models import DashboardStats, DashboardStatsCriteria
from admin_tools_stats.utils import BaseAuthenticatedClient, assertContainsAny

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from model_mommy import mommy


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
    def setUp(self):
        self.stats = mommy.make(
            'DashboardStats',
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
        )

    @override_settings(USE_TZ=False)
    def test_get_multi_series(self):
        """Test function to check dashboardstatscriteria admin pages"""
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
                "true": [False, "Active"]
            },
            use_as='multiple_series',
            id=5,
        )
        self.stats.criteria.add(criteria)
        self.stats.save()
        self.stats.refresh_from_db()
        mommy.make('User', date_joined=datetime.datetime(2010, 10, 10, tzinfo=datetime.timezone.utc))
        url = reverse('chart-data', kwargs={'graph_key': 'user_graph'})
        url += "?time_since=2010-10-08&time_until=2010-10-12&select_box_interval=days&select_box_chart_type=discreteBarChart&select_box_multiple_series=5"
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
                "CANCEL": "CANCEL"
            },
        )
        self.dashboard_stats_criteria.save()
        self.assertEqual(
            self.dashboard_stats_criteria.__str__(), 'call_type')

        # DashboardStats model
        self.dashboard_stats = DashboardStats(
            graph_key='user_graph_test',
            graph_title='User graph',
            model_app_name='auth',
            model_name='User',
            date_field_name='date_joined',
            is_visible=1,
        )
        self.dashboard_stats.save()
        self.dashboard_stats.criteria.add(self.dashboard_stats_criteria)
        self.dashboard_stats.save()
        with self.assertRaises(ValidationError) as e:
            self.dashboard_stats.clean()
        self.assertEqual(e.exception.message_dict, {})
        self.assertEqual(self.dashboard_stats.__str__(), 'user_graph_test')

    def test_dashboard_criteria(self):
        self.assertEqual(
            self.dashboard_stats_criteria.criteria_name, "call_type")
        self.assertEqual(self.dashboard_stats.graph_key, 'user_graph_test')

    def teardown(self):
        self.dashboard_stats_criteria.delete()
        self.dashboard_stats.delete()
