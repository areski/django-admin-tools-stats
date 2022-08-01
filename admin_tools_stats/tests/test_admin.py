from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from model_bakery import baker

from admin_tools_stats.models import DashboardStats, DashboardStatsCriteria

from .utils import BaseSuperuserAuthenticatedClient


class AdminIndexTests(BaseSuperuserAuthenticatedClient):
    def setUp(self):
        self.stats = baker.make(
            "DashboardStats",
            graph_title="User chart",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            operation_field_name="is_active,is_staff",
        )
        super().setUp()

    @override_settings(
        INSTALLED_APPS=[
            "django_nvd3",
            "admin_tools_stats",
            "admin_tools.menu",
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "djangobower",
            "demoproject",
        ]
    )
    def test_admin_index_empty(self):
        """Vanila admin index page without any chart, should note how to create it"""
        DashboardStats.objects.all().delete()
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertContains(
            response,
            "<p>No charts available, please "
            '<a href="/admin/admin_tools_stats/dashboardstats/">configure them</a></p>',
            html=True,
        )

    @override_settings(
        INSTALLED_APPS=[
            "django_nvd3",
            "admin_tools_stats",
            "admin_tools.menu",
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "djangobower",
            "demoproject",
        ]
    )
    def test_admin_index(self):
        """Test vanila admin index page, that should contain chart"""
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertContains(response, "<h3>User chart</h3>", html=True)
        self.assertContains(
            response,
            '<select name="select_box_operation_field" class="chart-input" required>'
            '<option value="">(divide all)</option>'
            '<option value="is_active" selected>is_active</option>'
            '<option value="is_staff">is_staff</option>'
            "</select>",
            html=True,
        )


class AdminToolsStatsAdminInterfaceTestCase(BaseSuperuserAuthenticatedClient):
    """
    Test cases for django-admin-tools-stats Admin Interface
    """

    def test_admin_tools_stats_dashboardstats(self):
        """Test function to check dashboardstats admin pages"""
        response = self.client.get("/admin/admin_tools_stats/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/admin/admin_tools_stats/dashboardstats/")
        self.assertEqual(response.status_code, 200)

    def test_admin_tools_stats_dashboardstatscriteria(self):
        """Test function to check dashboardstatscriteria admin pages"""
        response = self.client.get("/admin/admin_tools_stats/dashboardstatscriteria/")
        self.assertEqual(response.status_code, 200)


class AdminToolsStatsAdminCharts(BaseSuperuserAuthenticatedClient):
    def test_admin_dashboard_page(self):
        """Test function to check dashboardstatscriteria admin pages"""
        stats = baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            graph_title="User graph",
            model_name="User",
            model_app_name="auth",
        )
        baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            graph_title="User logged in graph",
            model_name="User",
            model_app_name="auth",
        )
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "": [None, "All"],
                "false": [False, "Inactive"],
                "true": [True, "Active"],
            },
        )
        baker.make("CriteriaToStatsM2M", criteria=criteria, stats=stats)
        response = self.client.get("/admin/")
        self.assertContains(
            response,
            "<h2>User graph</h2>",
            html=True,
        )
        self.assertContains(
            response,
            "<h2>User logged in graph</h2>",
            html=True,
        )
        self.assertContains(
            response,
            '<svg style="width:600px;height:400px;"></svg>',
            html=True,
        )
        self.assertContains(
            response,
            '<option value="True">Active</option>',
            html=True,
        )
        self.assertContains(
            response,
            '<option value="False">Inactive</option>',
            html=True,
        )

    def test_admin_dashboard_page_multi_series(self):
        stats = baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
        )
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "": [None, "All"],
                "false": [False, "Inactive"],
                "true": [True, "Active"],
            },
        )
        cm2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=stats,
            use_as="multiple_series",
        )
        stats.default_multiseries_criteria = cm2m
        stats.save()
        response = self.client.get("/admin/")
        self.assertContains(
            response,
            '<select name="select_box_multiple_series" '
            'class="chart-input select_box_multiple_series" required>'
            '<option value="">-------</option>'
            '<option value="2" selected>active</option>'
            "</select>",
            html=True,
        )

    def test_admin_dashboard_page_post(self):
        """Test function to check dashboardstatscriteria admin pages"""
        stats = baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
        )
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "": [None, "All"],
                "false": [False, "Inactive"],
                "true": [True, "Active"],
            },
        )
        baker.make("CriteriaToStatsM2M", criteria=criteria, stats=stats)
        response = self.client.post("/admin/", {"select_box_user_graph": "true"})
        self.assertContains(
            response,
            '<input type="hidden" class="hidden_graph_key" name="graph_key" value="user_graph">',
            html=True,
        )
        self.assertContains(
            response,
            '<option value="True">Active</option>',
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
            criteria_fix_mapping="",
            dynamic_criteria_field_name="disposition",
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
        self.assertEqual(self.dashboard_stats_criteria.__str__(), "call_type")

        # DashboardStats model
        self.dashboard_stats = baker.make(
            "DashboardStats",
            graph_key="user_graph_test",
            graph_title="User graph",
            model_app_name="auth",
            model_name="User",
            date_field_name="date_joined",
            is_visible=1,
        )
        baker.make(
            "CriteriaToStatsM2M",
            criteria=self.dashboard_stats_criteria,
            stats=self.dashboard_stats,
            use_as="multiple_series",
        )

    def test_dashboard_criteria(self):
        self.dashboard_stats.clean()
        self.assertEqual(self.dashboard_stats_criteria.criteria_name, "call_type")
        self.assertEqual(self.dashboard_stats.graph_key, "user_graph_test")
        self.assertEqual(self.dashboard_stats.__str__(), "user_graph_test")

    def tearDown(self):
        self.dashboard_stats_criteria.delete()
        self.dashboard_stats.delete()
