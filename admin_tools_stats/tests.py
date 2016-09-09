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

import django

from django.test import TestCase
from django.core.exceptions import ValidationError
from admin_tools_stats.models import DashboardStatsCriteria, DashboardStats
from admin_tools_stats.utils import BaseAuthenticatedClient


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

    if django.VERSION >= (1,8,0):
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
                '<input type="hidden" name="select_box_user_graph" value="true">',
                html=True,
            )
            self.assertContains(
                response,
                '<option value="true" selected="selected">Active</option>',
                html=True,
            )


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
