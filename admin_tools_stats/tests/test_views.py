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
from datetime import datetime, timezone

from django.contrib.auth.models import Permission
from django.test import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from model_bakery import baker

from admin_tools_stats.models import DashboardStats
from admin_tools_stats.views import AnalyticsView, ChartDataView, Interval

from .utils import (
    BaseSuperuserAuthenticatedClient,
    BaseUserAuthenticatedClient,
    assertContainsAny,
)


class AnalyticsViewTest(BaseSuperuserAuthenticatedClient):
    def setUp(self):
        self.stats = baker.make(
            "DashboardStats",
            graph_title="User chart",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            allowed_type_operation_field_name=["Sum", "Count"],
        )
        self.kid_stats = baker.make(
            "DashboardStats",
            graph_title="Kid chart",
            date_field_name="birthday",
            model_name="TestKid",
            model_app_name="demoproject",
            graph_key="kid_graph",
            operation_field_name="height",
        )
        super().setUp()

    def test_analytics_view_empty(self):
        """Test of analytics page when no charts are present"""
        DashboardStats.objects.all().delete()
        response = self.client.get(reverse("chart-analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "<p>No charts available, please "
            '<a href="/admin/admin_tools_stats/dashboardstats/">configure them</a></p>',
            html=True,
        )

    def test_analytics_view(self):
        """Test function to check dashboardstats admin pages"""
        response = self.client.get(reverse("chart-analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<button>Kid chart</button>", html=True)
        self.assertNotContains(response, "loadAnalyticsChart('")

    def test_analytics_view_show(self):
        """Test function to check dashboardstats admin pages that should show certain chart"""
        response = self.client.get(reverse("chart-analytics") + "?show=kid_graph")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<button>Kid chart</button>", html=True)
        self.assertContains(response, "loadAnalyticsChart('kid_graph')")

    def test_analytics_chart_view(self):
        """Test function to check dashboardstats admin pages"""
        response = self.client.get(reverse("chart-analytics", kwargs={"graph_key": "user_graph"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h3>User chart</h3>", html=True)
        self.assertContains(
            response,
            '<select name="select_box_operation" class="chart-input">'
            '<option value="Count">Count</option>'
            '<option value="Sum">Sum</option>'
            "</select>",
            html=True,
        )

    def test_get_charts_query(self):
        a = AnalyticsView()
        a.request = self.client.request()
        a.request.user = baker.make("User", is_superuser=True)
        self.assertQuerysetEqual(a.get_charts_query(), [self.kid_stats, self.stats])

    def test_get_charts_query_usser(self):
        a = AnalyticsView()
        kid_graph_user = baker.make(
            "DashboardStats",
            graph_title="Kid chart",
            date_field_name="birthday",
            model_name="TestKid",
            model_app_name="demoproject",
            graph_key="kid_graph_user",
            show_to_users=True,
        )
        a.request = self.client.request()
        a.request.user = baker.make("User")
        self.assertQuerysetEqual(a.get_charts_query(), [kid_graph_user])

    def test_get_templates_names(self):
        a = AnalyticsView()
        a.request = self.client.request()
        a.request.user = baker.make("User", is_superuser=True)
        self.assertEqual(a.get_template_names(), "admin_tools_stats/analytics.html")

    def test_get_templates_names_usser(self):
        a = AnalyticsView()
        a.request = self.client.request()
        a.request.user = baker.make("User")
        self.assertEqual(a.get_template_names(), "admin_tools_stats/analytics_user.html")


class MultiFieldViewsTests(BaseSuperuserAuthenticatedClient):
    def setUp(self):
        self.stats = baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            operation_field_name="is_active,is_staff",
        )
        super().setUp()

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_multiple_operations(self):
        """Test function view rendering multi series with multiple operations"""
        baker.make("User", date_joined=datetime(2010, 10, 10, tzinfo=timezone.utc))
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += (
            "?time_since=2010-10-08&time_until=2010-10-12&select_box_interval=days&"
            "select_box_chart_type=stackedAreaChart&select_box_operation_field="
        )
        response = self.client.get(url)
        assertContainsAny(
            self,
            response,
            ('{"x": 1286668800000, "y": 1}', '{"y": 1, "x": 1286668800000}'),
        )


class ChartDataViewContextTests(BaseSuperuserAuthenticatedClient):
    maxDiff = None

    def setUp(self):
        self.stats = baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            graph_title="Users chart",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            operation_field_name="is_active,is_staff",
        )
        self.kid_stats = baker.make(
            "DashboardStats",
            graph_title="Kid chart",
            date_field_name="birthday",
            model_name="TestKid",
            model_app_name="demoproject",
            graph_key="kid_graph",
            operation_field_name="height",
        )
        self.request_factory = RequestFactory()
        super().setUp()

    @override_settings(USE_TZ=True, TIME_ZONE="Europe/Prague")
    def test_get_context_no_permission(self):
        """
        Test function view rendering multi series with multiple operations
        Test no permissions
        """
        user = baker.make("User", date_joined=datetime(2010, 10, 10, tzinfo=timezone.utc))
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += (
            "?time_since=2010-10-08&time_until=2010-10-12&select_box_interval=days&"
            "select_box_chart_type=stackedAreaChart&select_box_operation_field="
        )
        chart_data_view = ChartDataView()
        chart_data_view.request = self.client.request(url=url)
        chart_data_view.request.user = user
        context = chart_data_view.get_context_data(graph_key="user_graph")
        self.assertEqual(
            context,
            {
                "error": "You have no permission to view this chart. "
                "Check if you are logged in and have permission "
                "'admin_tools_stats | dashboard stats | Can view dashboard stats'",
                "graph_title": "Users chart",
                "view": chart_data_view,
            },
        )

    def test_get_context(self):
        """
        Test function view rendering multi series with multiple operations
        """
        baker.make("User", date_joined=datetime(2010, 10, 10, tzinfo=timezone.utc))
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += (
            "?time_since=2010-10-08&time_until=2010-10-12&select_box_interval=days&"
            "select_box_chart_type=stackedAreaChart&select_box_operation_field=&debug=True"
        )
        chart_data_view = ChartDataView()
        chart_data_view.request = self.request_factory.get(url)
        chart_data_view.request.user = self.user
        context = chart_data_view.get_context_data(graph_key="user_graph")
        self.assertDictEqual(
            context,
            {
                "chart_container": "chart_container_user_graph",
                "chart_type": "stackedAreaChart",
                "extra": {
                    "tag_script_js": False,
                    "use_interactive_guideline": True,
                    "x_axis_format": "%d %b %Y",
                    "x_is_date": True,
                },
                "values": {
                    "extra1": {
                        "date_format": "%a %d %b %Y",
                        "tooltip": {"y_end": "", "y_start": ""},
                    },
                    "name0": "",
                    "name1": Interval.days,
                    "x": [
                        1286514000000,
                        1286600400000,
                        1286686800000,
                        1286773200000,
                        1286859600000,
                    ],
                    "y0": [0, 1, 0, 0, 0],
                },
                "view": chart_data_view,
            },
        )

    @override_settings(USE_TZ=True, TIME_ZONE="Europe/Prague")
    def test_get_context_tz(self):
        """
        Test function view rendering multi series with multiple operations
        Test correct context in more complicated timezone setting
        """
        baker.make("User", date_joined=datetime(2021, 10, 30, tzinfo=timezone.utc))
        baker.make("User", date_joined=datetime(2021, 10, 31, tzinfo=timezone.utc))
        baker.make("User", date_joined=datetime(2021, 11, 1, tzinfo=timezone.utc))
        baker.make("User", date_joined=datetime(2021, 11, 2, tzinfo=timezone.utc))
        baker.make("User", date_joined=datetime(2021, 11, 3, tzinfo=timezone.utc))
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += (
            "?time_since=2021-10-29&time_until=2021-11-05&select_box_interval=days&"
            "select_box_chart_type=stackedAreaChart&select_box_operation_field=&debug=True"
        )
        chart_data_view = ChartDataView()
        chart_data_view.request = self.request_factory.get(url)
        chart_data_view.request.user = self.user
        context = chart_data_view.get_context_data(graph_key="user_graph")
        self.assertDictEqual(
            context,
            {
                "chart_container": "chart_container_user_graph",
                "chart_type": "stackedAreaChart",
                "extra": {
                    "tag_script_js": False,
                    "use_interactive_guideline": True,
                    "x_axis_format": "%d %b %Y",
                    "x_is_date": True,
                },
                "values": {
                    "extra1": {
                        "date_format": "%a %d %b %Y",
                        "tooltip": {"y_end": "", "y_start": ""},
                    },
                    "name0": "",
                    "name1": Interval.days,
                    "x": [
                        1635458400000,  # 2021-10-28 22:00:00 GMT
                        1635544800000,
                        1635631200000,
                        1635721200000,
                        1635807600000,
                        1635894000000,
                        1635980400000,
                        1636066800000,  # 2021-11-04 23:00:00 GMT
                    ],
                    "y0": [0, 1, 1, 1, 1, 1, 0, 0],
                },
                "view": chart_data_view,
            },
        )

    @override_settings(USE_TZ=True, TIME_ZONE="Europe/Prague")
    def test_get_context_tz_operation(self):
        """
        Test function view rendering multi series with multiple operations
        Test correct context in more complicated timezone setting
        Set select_box_operation field
        """
        baker.make("TestKid", birthday=datetime(2021, 10, 30, tzinfo=timezone.utc), height=150)
        baker.make("TestKid", birthday=datetime(2021, 10, 31, tzinfo=timezone.utc), height=160)
        baker.make("TestKid", birthday=datetime(2021, 11, 1, tzinfo=timezone.utc), height=170)
        baker.make("TestKid", birthday=datetime(2021, 11, 2, tzinfo=timezone.utc), height=180)
        baker.make("TestKid", birthday=datetime(2021, 11, 3, tzinfo=timezone.utc), height=190)
        baker.make("TestKid", birthday=datetime(2021, 11, 3, tzinfo=timezone.utc), height=210)
        url = reverse("chart-data", kwargs={"graph_key": "kid_graph"})
        url += (
            "?time_since=2021-10-29&time_until=2021-11-05&select_box_interval=days&"
            "select_box_chart_type=stackedAreaChart&select_box_operation_field=&debug=True&"
            "select_box_operation=Avg"
        )
        chart_data_view = ChartDataView()
        chart_data_view.request = self.request_factory.get(url)
        chart_data_view.request.user = self.user
        context = chart_data_view.get_context_data(graph_key="kid_graph")
        self.assertDictEqual(
            context,
            {
                "chart_container": "chart_container_kid_graph",
                "chart_type": "stackedAreaChart",
                "extra": {
                    "tag_script_js": False,
                    "use_interactive_guideline": True,
                    "x_axis_format": "%d %b %Y",
                    "x_is_date": True,
                },
                "values": {
                    "extra1": {
                        "date_format": "%a %d %b %Y",
                        "tooltip": {"y_end": "", "y_start": ""},
                    },
                    "name0": "",
                    "name1": Interval.days,
                    "x": [
                        1635458400000,  # 2021-10-28 22:00:00 GMT
                        1635544800000,
                        1635631200000,
                        1635721200000,
                        1635807600000,
                        1635894000000,
                        1635980400000,
                        1636066800000,  # 2021-11-04 23:00:00 GMT
                    ],
                    "y0": [0, 150, 160, 170, 180, 200, 0, 0],
                },
                "view": chart_data_view,
            },
        )


class SuperuserViewsTests(BaseSuperuserAuthenticatedClient):
    def setUp(self):
        self.stats = baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            y_axis_format="%s",
        )
        super().setUp()

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series(self):
        """Test function view rendering multi series"""
        baker.make("User", date_joined=datetime(2010, 10, 10, tzinfo=timezone.utc))
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += (
            "?time_since=2010-10-08&time_until=2010-10-12"
            "&select_box_interval=days&select_box_chart_type=discreteBarChart"
        )
        response = self.client.get(url)
        assertContainsAny(
            self,
            response,
            ('{"x": 1286668800000, "y": 1}', '{"y": 1, "x": 1286668800000}'),
        )

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_cached(self):
        """Test function view rendering multi series"""
        self.stats.cache_values = True
        self.stats.save()

        baker.make(
            "CachedValue",
            stats=self.stats,
            time_scale="days",
            operation=None,
            dynamic_choices=[],
            filtered_value="",
            date=datetime(2010, 10, 10, tzinfo=timezone.utc),
            value=1,
        )
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += (
            "?time_since=2010-10-08&time_until=2010-10-12"
            "&select_box_interval=days&select_box_chart_type=lineChart"
        )
        response = self.client.get(url)
        assertContainsAny(
            self,
            response,
            ('{"x": 1286668800000, "y": 1.0}', '{"y": 1.0, "x": 1286668800000}'),
        )

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_since_gt_until(self):
        """
        Test function view rendering multi series
        returns error if since is greater than until
        """
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += "?time_since=2010-11-08&time_until=2010-10-12"
        response = self.client.get(url)
        self.assertContains(
            response,
            "Time since is greater than time until",
        )

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_fault_date(self):
        """
        Test function view rendering multi series
        returns error if date is faulty
        """
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += "?time_since=2010-10-08&time_until=2010-13-12"
        response = self.client.get(url)
        self.assertContains(
            response,
            b"time data \\u00272010\\u002D13\\u002D12\\u0027 "
            b"does not match format \\u0027%Y\\u002D%m\\u002D%d\\u0027",
        )

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_fault_date_debug(self):
        """
        Test function view rendering multi series
        returns error if date is faulty
        """
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += "?time_since=2010-10-08&time_until=2010-13-12&debug=True"
        with self.assertRaisesRegex(
            ValueError, "^time data '2010-13-12' does not match format '%Y-%m-%d'$"
        ):
            self.client.get(url)

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_dynamic_criteria(self):
        """Test function view rendering multi series with dynamic criteria"""
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "": [None, "All"],
                "false": [True, "Inactive"],
                "true": [False, "Active"],
            },
        )
        baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
            id=5,
        )
        baker.make("User", date_joined=datetime(2010, 10, 10, tzinfo=timezone.utc))
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += "?time_since=2010-10-08"
        url += "&time_until=2010-10-12"
        url += "&select_box_interval=days"
        url += "&select_box_chart_type=discreteBarChart"
        url += "&select_box_multiple_series=5"
        url += "&debug=True"
        response = self.client.get(url)
        self.assertContains(response, ('"key": "Inactive"'))
        self.assertContains(response, ('"key": "Active"'))


class UserViewsTests(BaseUserAuthenticatedClient):
    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_no_permissions_not_enabled(self):
        baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            user_field_name=None,
            show_to_users=False,
        )
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += (
            "?time_since=2010-10-08&time_until=2010-10-12&select_box_interval=days"
            "&select_box_chart_type=discreteBarChart"
        )
        response = self.client.get(url)
        self.assertContains(
            response,
            "You have no permission to view this chart. Check if you are logged in",
        )

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_no_permissions(self):
        baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            user_field_name=None,
            show_to_users=True,
        )
        permission = Permission.objects.get(codename="view_dashboardstats")
        self.user.user_permissions.add(permission)
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += (
            "?time_since=2010-10-08&time_until=2010-10-12&select_box_interval=days"
            "&select_box_chart_type=discreteBarChart"
        )
        response = self.client.get(url)
        assertContainsAny(
            self,
            response,
            ('{"x": 1286668800000, "y": 0}', '{"y": 0, "x": 1286668800000}'),
        )

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_user_chart(self):
        baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            user_field_name=None,
            show_to_users=True,
        )
        url = reverse("chart-data", kwargs={"graph_key": "user_graph"})
        url += (
            "?time_since=2010-10-08&time_until=2010-10-12&select_box_interval=days&"
            "select_box_chart_type=discreteBarChart"
        )
        response = self.client.get(url)
        assertContainsAny(
            self,
            response,
            ('{"x": 1286668800000, "y": 0}', '{"y": 0, "x": 1286668800000}'),
        )
