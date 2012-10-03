
from django.test import TestCase
from admin_tools_stats.models import DashboardStatsCriteria, DashboardStats
from common.utils import BaseAuthenticatedClient


class AdminToolsStatsAdminInterfaceTestCase(BaseAuthenticatedClient):
    """Test cases for django-admin-tools-stats Admin Interface."""

    def test_admin_tools_stats_dashboardstats(self):
        """Test function to check dashboardstats admin pages"""
        response = self.client.get('/admin/admin_tools_stats/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/admin_tools_stats/dashboardstats/')
        self.failUnlessEqual(response.status_code, 200)

    def test_admin_tools_stats_dashboardstatscriteria(self):
        """Test function to check dashboardstatscriteria admin pages"""
        response = \
            self.client.get('/admin/admin_tools_stats/dashboardstatscriteria/')
        self.failUnlessEqual(response.status_code, 200)


class AdminToolsStatsModel(TestCase):
    """
    Test DashboardStatsCriteria, DashboardStats models
    """

    #fixtures = []

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
            self.dashboard_stats_criteria.__unicode__(), 'call_type')

        # DashboardStats model
        self.dashboard_stats = DashboardStats(
            graph_key='user_graph',
            graph_title='User graph',
            model_app_name='auth',
            model_name='User',
            date_field_name='date_joined',
            criteria=self.dashboard_stats_criteria,
            is_visible=1,
        )
        self.dashboard_stats.save()
        self.assertEqual(self.dashboard_stats.__unicode__(), 'user_graph')

    def test_dashboard_criteria(self):
        self.assertEqual(
            self.dashboard_stats_criteria.criteria_name, "call_type")
        self.assertEqual(self.dashboard_stats.graph_key, 'user_graph')

    def teardown(self):
        self.dashboard_stats_criteria.delete()
        self.dashboard_stats.delete()
