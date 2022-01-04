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
from unittest import skipIf

import django
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.aggregates import Avg, Count, Max, Min, StdDev, Sum, Variance
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from model_mommy import mommy

from admin_tools_stats.models import CachedValue


try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

UTC = datetime.timezone.utc


class DashboardStatsCriteriaTests(TestCase):
    def test_criteria_dynamic_mapping_preview(self):
        """
        Test criteria_dynamic_mapping_preview() function
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            criteria_dynamic_mapping="{'foo': 'bar'}",
        )
        self.assertEqual(criteria.criteria_dynamic_mapping_preview(), "{'foo': 'bar'}")

    def test_criteria_dynamic_mapping_preview_blank(self):
        """
        Test criteria_dynamic_mapping_preview() function
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
        )
        self.assertEqual(criteria.criteria_dynamic_mapping_preview(), "")

    def test_criteria_dynamic_mapping_preview_long(self):
        """
        Test criteria_dynamic_mapping_preview() function
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            criteria_dynamic_mapping="{'foo': 'bar" + "a" * 105 + "'}",
        )
        result = criteria.criteria_dynamic_mapping_preview()
        self.assertTrue("{'foo': 'baraaaaaa" in result)
        self.assertTrue("aaaaaa..." in result)
        self.assertEquals(len(result), 103)

    def test_criteria_m2m_get_dynamic_criteria_field_name_prefix(self):
        """
        Test get_dynamic_criteria_field_name() function
        """
        criteria = mommy.make(
            "CriteriaToStatsM2M",
            criteria__dynamic_criteria_field_name="field_name",
            prefix="related__",
        )
        result = criteria.get_dynamic_criteria_field_name()
        self.assertEquals(result, "related__field_name")


class ModelTests(TestCase):
    maxDiff = None

    def setUp(self):
        self.stats = mommy.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
        )
        self.kid_stats = mommy.make(
            "DashboardStats",
            date_field_name="birthday",
            model_name="TestKid",
            model_app_name="demoproject",
            graph_key="kid_graph",
        )

    def test_clean(self):
        self.stats.clean()

    def test_clean_error_model_app_app_name(self):
        self.stats.model_app_name = ("auth1",)
        with self.assertRaises(ValidationError) as e:
            self.stats.clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "model_app_name": ["No installed app with label 'auth1'."],
                "model_name": ["No installed app with label 'auth1'."],
            },
        )

    def test_clean_error_model_name(self):
        self.stats.model_name = "User1"
        with self.assertRaises(ValidationError) as e:
            self.stats.clean()
        self.assertEqual(
            e.exception.message_dict,
            {"model_name": ["App 'auth' doesn't have a 'User1' model."]},
        )

    def test_clean_error_operation_field(self):
        self.stats.operation_field_name = "asdf"
        with self.assertRaises(ValidationError) as e:
            self.stats.clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "operation_field_name": [
                    "Cannot resolve keyword 'asdf' into field. Choices are: "
                    "bookmark, dashboardpreferences, date_joined, email, "
                    "first_name, groups, id, is_active, is_staff, "
                    "is_superuser, last_login, last_name, logentry, password, "
                    "testkid, user_permissions, username"
                ]
            },
        )

    def test_clean_error_date_field(self):
        self.stats.date_field_name = "asdf"
        with self.assertRaises(ValidationError) as e:
            self.stats.clean()
        self.assertEqual(
            e.exception.message_dict,
            {
                "date_field_name": [
                    "Cannot resolve keyword 'asdf' into field. Choices are: "
                    "bookmark, dashboardpreferences, date_joined, email, "
                    "first_name, groups, id, is_active, is_staff, "
                    "is_superuser, last_login, last_name, logentry, password, "
                    "testkid, user_permissions, username"
                ]
            },
        )

    maxDiff = None

    def test_get_operation(self):
        stats = mommy.make(
            "DashboardStats",
            model_name="TestKid",
            model_app_name="demoproject",
            operation_field_name="age,height",
        )
        self.assertEqual(
            stats.get_operation("Count", ""), Count("age", distinct=False, filter=None)
        )
        self.assertEqual(stats.get_operation("Sum", ""), Sum("age"))
        self.assertEqual(stats.get_operation("Avg", ""), Avg("age"))
        self.assertEqual(stats.get_operation("StdDev", ""), StdDev("age", filter=None))
        self.assertEqual(stats.get_operation("Max", ""), Max("age"))
        self.assertEqual(stats.get_operation("Min", ""), Min("age"))
        self.assertEqual(stats.get_operation("Variance", ""), Variance("age", filter=None))
        self.assertEqual(
            str(stats.get_operation("AvgCountPerInstance", "")),
            "ExpressionWrapper(Value(1.0) * Count(F(age)) / Count(F(id), "
            "distinct=True, filter=(AND: ('age__isnull', False))))",
        )

    @skipIf(django.VERSION[0] < 3, "Django < 3 doesn't support distinct Avg, Sum, ...")
    def test_get_operation_distinct(self):
        stats = mommy.make(
            "DashboardStats",
            model_name="TestKid",
            model_app_name="demoproject",
            distinct=True,
            operation_field_name="age,height",
        )
        self.assertEqual(stats.get_operation("Count", ""), Count("age", distinct=True, filter=None))
        self.assertEqual(stats.get_operation("Sum", ""), Sum("age", distinct=True))
        self.assertEqual(stats.get_operation("Avg", ""), Avg("age", distinct=True))
        self.assertEqual(stats.get_operation("StdDev", ""), StdDev("age", filter=None))
        self.assertEqual(stats.get_operation("Max", ""), Max("age"))
        self.assertEqual(stats.get_operation("Min", ""), Min("age"))
        self.assertEqual(stats.get_operation("Variance", ""), Variance("age", filter=None))
        self.assertEqual(
            str(stats.get_operation("AvgCountPerInstance", "")),
            "ExpressionWrapper(Value(1.0) * Count(F(age), distinct=True) / Count(F(id), "
            "distinct=True, filter=(AND: ('age__isnull', False))))",
        )

    def test_get_operation_no_operation_choice(self):
        stats = mommy.make(
            "DashboardStats",
            model_name="TestKid",
            model_app_name="demoproject",
            operation_field_name=",height",
        )
        self.assertEqual(stats.get_operation("Count", ""), Count("id", distinct=False, filter=None))
        self.assertEqual(stats.get_operation("Sum", ""), Sum("id"))
        self.assertEqual(stats.get_operation("Avg", ""), Avg("id"))
        self.assertEqual(stats.get_operation("StdDev", ""), StdDev("id", filter=None))
        self.assertEqual(stats.get_operation("Max", ""), Max("id"))
        self.assertEqual(stats.get_operation("Min", ""), Min("id"))
        self.assertEqual(stats.get_operation("Variance", ""), Variance("id", filter=None))
        self.assertEqual(
            str(stats.get_operation("AvgCountPerInstance", "")),
            "ExpressionWrapper(Value(1.0) * Count(F(id)) / Count(F(id), "
            "distinct=True, filter=(AND: ('id__isnull', False))))",
        )

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 10))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 10, 12)

        interval = "days"
        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {"": 0},
            datetime.datetime(2010, 10, 9, 0, 0): {"": 0},
            datetime.datetime(2010, 10, 10, 0, 0): {"": 1},
            datetime.datetime(2010, 10, 11, 0, 0): {"": 0},
            datetime.datetime(2010, 10, 12, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_m2m_prefix(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        with m2m criteria with related prefix
        """
        user = mommy.make("User", first_name="Milos", is_superuser=True)
        mommy.make("TestKid", author=user, birthday=datetime.date(2010, 10, 10))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 10, 12)
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.kid_stats,
            prefix="author__",
            use_as="multiple_series",
            choices_based_on_time_range=True,
        )

        interval = "days"
        serie = self.kid_stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            interval,
            None,
            None,
            user,
        )
        testing_data = {
            datetime.date(2010, 10, 8): {"Milos": 0},
            datetime.date(2010, 10, 9): {"Milos": 0},
            datetime.date(2010, 10, 10): {"Milos": 1},
            datetime.date(2010, 10, 11): {"Milos": 0},
            datetime.date(2010, 10, 12): {"Milos": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_time_based_choices(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Choices are based on time range
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
            choices_based_on_time_range=True,
        )
        user = mommy.make(
            "User",
            date_joined=datetime.date(2010, 10, 10),
            first_name="Petr",
            is_superuser=True,
        )
        mommy.make("User", date_joined=datetime.date(2010, 10, 9), first_name="Adam")
        mommy.make("User", date_joined=datetime.date(2010, 10, 15), first_name="Jirka")
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 10, 12)

        interval = "days"
        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            interval,
            None,
            None,
            user,
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {"Adam": 0, "Petr": 0},
            datetime.datetime(2010, 10, 9, 0, 0): {"Adam": 1, "Petr": 0},
            datetime.datetime(2010, 10, 10, 0, 0): {"Adam": 0, "Petr": 1},
            datetime.datetime(2010, 10, 11, 0, 0): {"Adam": 0, "Petr": 0},
            datetime.datetime(2010, 10, 12, 0, 0): {"Adam": 0, "Petr": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_count_limit(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Choices are limited by count
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
            count_limit=1,
        )
        user = mommy.make(
            "User",
            date_joined=datetime.date(2010, 10, 10),
            first_name="Petr",
            is_superuser=True,
        )
        mommy.make("User", date_joined=datetime.date(2010, 10, 10), first_name="Petr")
        mommy.make("User", date_joined=datetime.date(2010, 10, 9), first_name="Adam")
        mommy.make("User", date_joined=datetime.date(2010, 10, 11), first_name="Jirka")
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 10, 12)

        interval = "days"
        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            interval,
            None,
            None,
            user,
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {"other": 0, "Petr": 0},
            datetime.datetime(2010, 10, 9, 0, 0): {"other": 1, "Petr": 0},
            datetime.datetime(2010, 10, 10, 0, 0): {"other": 0, "Petr": 2},
            datetime.datetime(2010, 10, 11, 0, 0): {"other": 1, "Petr": 0},
            datetime.datetime(2010, 10, 12, 0, 0): {"other": 0, "Petr": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_hours(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make("User", date_joined=datetime.datetime(2010, 10, 8, 23, 13))
        time_since = datetime.datetime(2010, 10, 8, 22)
        time_until = datetime.datetime(2010, 10, 8, 23, 59)

        interval = "hours"
        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 22, 0): {"": 0},
            datetime.datetime(2010, 10, 8, 23, 0): {"": 1},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_weeks(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 30))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 11, 8)

        interval = "weeks"
        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 4, 0, 0): {"": 0},
            datetime.datetime(2010, 10, 11, 0, 0): {"": 0},
            datetime.datetime(2010, 10, 18, 0, 0): {"": 0},
            datetime.datetime(2010, 10, 25, 0, 0): {"": 1},
            datetime.datetime(2010, 11, 1, 0, 0): {"": 0},
            datetime.datetime(2010, 11, 8, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_months(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 30))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 11, 30)

        interval = "months"
        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 1, 0, 0): {"": 1},
            datetime.datetime(2010, 11, 1, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_quarters(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 30))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2011, 10, 8)

        interval = "quarters"
        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 1, 0, 0): {"": 1},
            datetime.datetime(2011, 1, 1, 0, 0): {"": 0},
            datetime.datetime(2011, 4, 1, 0, 0): {"": 0},
            datetime.datetime(2011, 7, 1, 0, 0): {"": 0},
            datetime.datetime(2011, 10, 1, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_years(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 30))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2011, 10, 8)

        interval = "years"
        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 1, 1, 0, 0): {"": 1},
            datetime.datetime(2011, 1, 1, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="Europe/Prague")
    def test_get_multi_series_datetime_tz(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        current_tz = timezone.get_current_timezone()
        user = mommy.make("User", date_joined=datetime.datetime(2010, 10, 10, tzinfo=current_tz))
        mommy.make(
            "User",
            date_joined=datetime.datetime(2010, 10, 10, 12, 34, tzinfo=current_tz),
        )
        time_since = datetime.datetime(2010, 10, 9, 0, 0)
        time_until = datetime.datetime(2010, 10, 11, 0, 0)

        interval = "days"
        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 2},
            datetime.datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="CET")
    def test_get_multi_series_date_tz(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        mommy.make("TestKid", birthday=datetime.date(2010, 10, 10))
        mommy.make("TestKid", birthday=None)
        time_since = datetime.datetime(2010, 10, 9)
        time_until = datetime.datetime(2010, 10, 11)

        interval = "days"
        user = mommy.make("User")
        serie = self.kid_stats.get_multi_time_series(
            {}, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.date(2010, 10, 9): {"": 0},
            datetime.date(2010, 10, 10): {"": 1},
            datetime.date(2010, 10, 11): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="Europe/Prague")
    def test_get_multi_series_change_dst(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        on edge of daylight saving time change
        """
        current_tz = zoneinfo.ZoneInfo("Europe/Prague")
        user = mommy.make(
            "User", date_joined=datetime.datetime(2019, 10, 28).astimezone(current_tz)
        )
        time_since = datetime.datetime(2019, 10, 27, 0, 0)
        time_until = datetime.datetime(2019, 10, 29, 0, 0)

        interval = "days"
        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2019, 10, 27, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2019, 10, 28, 0, 0).astimezone(current_tz): {"": 1},
            datetime.datetime(2019, 10, 29, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_distinct_count(self):
        """Test function to check DashboardStats.get_multi_time_series() with distinct count."""
        stats = mommy.make(
            "DashboardStats",
            model_name="User",
            date_field_name="date_joined",
            model_app_name="auth",
            type_operation_field_name="Count",
            distinct=True,
            operation_field_name="first_name",
        )
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 10), first_name="Foo")
        mommy.make("User", date_joined=datetime.date(2010, 10, 10), first_name="Foo")
        mommy.make("User", date_joined=datetime.date(2010, 10, 10), first_name="Bar")
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 10, 12)

        interval = "days"
        serie = stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {"": 0},
            datetime.datetime(2010, 10, 9, 0, 0): {"": 0},
            datetime.datetime(2010, 10, 10, 0, 0): {"": 2},
            datetime.datetime(2010, 10, 11, 0, 0): {"": 0},
            datetime.datetime(2010, 10, 12, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
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
                "DashboardStats",
                model_name="TestKid",
                date_field_name="birthday",
                model_app_name="demoproject",
                type_operation_field_name=func,
                operation_field_name="age",
            )
            mommy.make("TestKid", birthday=datetime.date(2010, 10, 10), age=12)
            mommy.make("TestKid", birthday=datetime.date(2010, 10, 10), age=1)
            mommy.make("TestKid", birthday=datetime.date(2010, 10, 10), age=2)
            mommy.make("TestKid", birthday=None)
            time_since = datetime.datetime(2010, 10, 9)
            time_until = datetime.datetime(2010, 10, 10)

            interval = "days"
            user = mommy.make("User")
            serie = stats.get_multi_time_series(
                {}, time_since, time_until, interval, None, None, user
            )
            self.assertEqual(
                serie[datetime.date(2010, 10, 10)][""],
                result,
                "Bad value for function %s" % func,
            )

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_dynamic_field_name(self):
        """Test function to check DashboardStats.get_multi_time_series() with dynamic criteria mapping"""
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "": [None, "All"],
                "false": [False, "Inactive"],
                "true": [True, "Active"],
            },
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 12), is_active=True)
        mommy.make("User", date_joined=datetime.date(2010, 10, 13), is_active=False)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            interval,
            None,
            None,
            user,
        )
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((("Active", 1), ("Inactive", 0))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((("Active", 0), ("Inactive", 1))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_dynamic_field_name_old_format(self):
        """
        Test function to check DashboardStats.get_multi_time_series() with dynamic criteria mapping
        the criteria is given in old format
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "False": "Inactive",
                "True": "Active",
            },
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 12), is_active=True)
        mommy.make("User", date_joined=datetime.date(2010, 10, 13), is_active=False)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            interval,
            None,
            None,
            user,
        )
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((("Active", 1), ("Inactive", 0))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((("Active", 0), ("Inactive", 1))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_criteria_without_dynamic_mapping(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        DashboardStatsCriteria is set, but without dynamic mapping, so the values are autogenerated.
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 12), is_active=True)
        mommy.make("User", date_joined=datetime.date(2010, 10, 13), is_active=False)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            interval,
            None,
            None,
            user,
        )
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((("True", 0), ("False", 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((("True", 0), ("False", 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((("True", 1), ("False", 0))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((("True", 0), ("False", 1))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((("True", 0), ("False", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_criteria_without_dynamic_mapping_choices(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        DashboardStatsCriteria is set, but without dynamic mapping,
        so the values are autogenerated on CharField.
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        mommy.make("User", date_joined=datetime.date(2010, 10, 12), last_name="Foo")
        mommy.make("User", date_joined=datetime.date(2010, 10, 13), last_name="Bar")
        mommy.make("User", date_joined=datetime.date(2010, 10, 14))
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        user = mommy.make("User", is_superuser=True)
        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            interval,
            None,
            None,
            user,
        )
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((("Bar", 0), ("Foo", 1))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((("Bar", 1), ("Foo", 0))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_criteria_combine(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Try to combine multiple_series filter with chart_filter.
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        criteria_active = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        m2m_active = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria_active,
            stats=self.stats,
            use_as="chart_filter",
        )
        mommy.make(
            "User",
            date_joined=datetime.date(2010, 10, 12),
            last_name="Foo",
            is_active=True,
        )
        mommy.make(
            "User",
            date_joined=datetime.date(2010, 10, 13),
            last_name="Bar",
            is_active=False,
        )
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        user = mommy.make("User", is_superuser=True)
        arguments = {
            "select_box_multiple_series": m2m.id,
            "select_box_dynamic_%s" % m2m_active.id: "True",
        }
        serie = self.stats.get_multi_time_series(
            arguments, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((("Bar", 0), ("Foo", 1))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_criteria_combine_user_exception(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        If user has no permission and user field is not defined, exception must be thrown.
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        user = mommy.make("User")
        arguments = {"select_box_multiple_series": m2m.id}
        with self.assertRaisesRegex(
            Exception,
            "^User field must be defined to enable charts for non-superusers$",
        ):
            self.stats.get_multi_time_series(
                arguments, time_since, time_until, interval, None, None, user
            )

    @skipIf(django.VERSION[0] < 3, "Django < 3 doesn't support Sum")
    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_criteria_user(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Check results, if stats are displayed for user
        """
        stats = mommy.make(
            "DashboardStats",
            model_name="TestKid",
            date_field_name="appointment",
            model_app_name="demoproject",
            type_operation_field_name="Sum",
            distinct=True,
            operation_field_name="age",
            user_field_name="author",
        )
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="name",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=stats,
            use_as="multiple_series",
        )
        user = mommy.make("User")
        mommy.make(
            "TestKid",
            appointment=datetime.date(2010, 10, 12),
            name="Foo",
            age=5,
            author=user,
        )
        mommy.make(
            "TestKid",
            appointment=datetime.date(2010, 10, 13),
            name="Bar",
            age=7,
            author=user,
        )
        mommy.make("TestKid", appointment=datetime.date(2010, 10, 13), name="Bar", age=7)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        arguments = {"select_box_multiple_series": m2m.id}
        serie = stats.get_multi_time_series(
            arguments, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0, tzinfo=UTC): OrderedDict(
                (("Bar", 0), ("Foo", 0))
            ),
            datetime.datetime(2010, 10, 11, 0, 0, tzinfo=UTC): OrderedDict(
                (("Bar", 0), ("Foo", 0))
            ),
            datetime.datetime(2010, 10, 12, 0, 0, tzinfo=UTC): OrderedDict(
                (("Bar", None), ("Foo", 5))
            ),
            datetime.datetime(2010, 10, 13, 0, 0, tzinfo=UTC): OrderedDict(
                (("Bar", 7), ("Foo", None))
            ),
            datetime.datetime(2010, 10, 14, 0, 0, tzinfo=UTC): OrderedDict(
                (("Bar", 0), ("Foo", 0))
            ),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(django.VERSION[0] < 3, "Django < 3 doesn't support distinct Avg")
    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_criteria_isnull(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Check __isnull criteria
        """
        stats = mommy.make(
            "DashboardStats",
            model_name="TestKid",
            date_field_name="appointment",
            model_app_name="demoproject",
            type_operation_field_name="Avg",
            distinct=True,
            operation_field_name="age",
        )
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="birthday",
            dynamic_criteria_field_name="birthday__isnull",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=stats,
            use_as="multiple_series",
        )
        mommy.make(
            "TestKid",
            appointment=datetime.date(2010, 10, 12),
            birthday=datetime.date(2010, 11, 12),
            age=4,
        )
        mommy.make("TestKid", appointment=datetime.date(2010, 10, 13), birthday=None, age=3)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        arguments = {"select_box_multiple_series": m2m.id}
        user = mommy.make("User", is_staff=True)
        serie = stats.get_multi_time_series(
            arguments, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0, tzinfo=UTC): {"Blank": 0, "Non blank": 0},
            datetime.datetime(2010, 10, 11, 0, 0, tzinfo=UTC): {"Blank": 0, "Non blank": 0},
            datetime.datetime(2010, 10, 12, 0, 0, tzinfo=UTC): {"Blank": None, "Non blank": 4},
            datetime.datetime(2010, 10, 13, 0, 0, tzinfo=UTC): {"Blank": 3, "Non blank": None},
            datetime.datetime(2010, 10, 14, 0, 0, tzinfo=UTC): {"Blank": 0, "Non blank": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_criteria_multiple_operations(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Test case with multiple operations and no operation field set
        """
        stats = mommy.make(
            "DashboardStats",
            model_name="TestKid",
            date_field_name="appointment",
            model_app_name="demoproject",
            type_operation_field_name="Sum",
            operation_field_name="age, height",
        )
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="birthday",
            dynamic_criteria_field_name="birthday__isnull",
        )
        mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=stats,
            use_as="multiple_series",
        )
        mommy.make(
            "TestKid",
            appointment=datetime.date(2010, 10, 12),
            birthday=datetime.date(2010, 11, 12),
            age=4,
            height=60,
        )
        mommy.make(
            "TestKid", appointment=datetime.date(2010, 10, 13), birthday=None, age=3, height=50
        )
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        arguments = {"operation_choice": ""}
        user = mommy.make("User", is_staff=True)
        serie = stats.get_multi_time_series(
            arguments, time_since, time_until, interval, "", None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0, tzinfo=UTC): {"age": 0, "height": 0},
            datetime.datetime(2010, 10, 11, 0, 0, tzinfo=UTC): {"age": 0, "height": 0},
            datetime.datetime(2010, 10, 12, 0, 0, tzinfo=UTC): {"age": 4, "height": 60},
            datetime.datetime(2010, 10, 13, 0, 0, tzinfo=UTC): {"age": 3, "height": 50},
            datetime.datetime(2010, 10, 14, 0, 0, tzinfo=UTC): {"age": 0, "height": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_fixed_criteria(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Try to combine multiple_series filter with chart_filter.
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        criteria_active = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            criteria_fix_mapping={"is_active": True},
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria_active,
            stats=self.stats,
            use_as="chart_filter",
        )
        mommy.make(
            "User",
            date_joined=datetime.date(2010, 10, 12),
            last_name="Foo",
            is_active=True,
        )
        mommy.make(
            "User",
            date_joined=datetime.date(2010, 10, 13),
            last_name="Bar",
            is_active=False,
        )
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        arguments = {"select_box_multiple_series": m2m.id}
        user = mommy.make("User", is_superuser=True)
        serie = self.stats.get_multi_time_series(
            arguments, time_since, time_until, interval, None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((("Bar", 0), ("Foo", 1))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    def test_no_user_field_name(self):
        """
        Test that non-superuser without user_field_name can't see charts
        """
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        mommy.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            criteria_fix_mapping={"is_active": True},
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        user = mommy.make(
            "User",
            date_joined=datetime.date(2010, 10, 12),
            last_name="Foo",
            is_active=True,
        )
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)
        arguments = {"select_box_multiple_series": m2m.id}
        with self.assertRaises(Exception):
            self.stats.get_multi_time_series(arguments, time_since, time_until, "days", None, user)


class CacheModelTests(TestCase):
    maxDiff = None

    def setUp(self):
        self.stats = mommy.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
        )
        common_parameters = {
            "stats": self.stats,
            "time_scale": "days",
            "operation": None,
            "dynamic_choices": [],
            "filtered_value": "",
        }
        current_tz = timezone.get_current_timezone()
        mommy.make(
            "CachedValue",
            **common_parameters,
            date=datetime.datetime(2010, 10, 9).astimezone(current_tz),
            value=3,
        )
        mommy.make(
            "CachedValue",
            **common_parameters,
            date=datetime.datetime(2010, 10, 11).astimezone(current_tz),
            value=5,
        )
        mommy.make(
            "CachedValue",
            **common_parameters,
            date=datetime.datetime(2010, 10, 12).astimezone(current_tz),
            is_final=False,
            value=5,
        )

    def test_get_multi_series_cached(self):
        """Simple test of DashboardStats.get_multi_time_series_cached() same as the variant without cache"""
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 10))
        CachedValue.objects.all().delete()
        current_tz = timezone.get_current_timezone()
        time_since = datetime.datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime.datetime(2010, 10, 12).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {}, time_since, time_until, "days", None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime.datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_cached_values(self):
        """Test DashboardStats.get_multi_time_series_cached() if some values were already in cache"""
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 10))
        current_tz = timezone.get_current_timezone()
        time_since = datetime.datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime.datetime(2010, 10, 13).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {}, time_since, time_until, "days", None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 3},
            datetime.datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime.datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 5},
            datetime.datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 5},
            datetime.datetime(2010, 10, 13, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_cached_values_reload(self):
        """Same as test above, but the data reload is requested"""
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 10))
        current_tz = timezone.get_current_timezone()
        time_since = datetime.datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime.datetime(2010, 10, 13).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {"reload": "True"}, time_since, time_until, "days", None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 3},
            datetime.datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime.datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 5},
            datetime.datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 13, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_cached_values_reload_all(self):
        """Same as test above, but reload of all data is requested"""
        user = mommy.make("User", date_joined=datetime.date(2010, 10, 10))
        current_tz = timezone.get_current_timezone()
        time_since = datetime.datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime.datetime(2010, 10, 13).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {"reload_all": "True"}, time_since, time_until, "days", None, None, user
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime.datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 13, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    def test_choices_based_on_time_range(self):
        """Same as test above, but reload of all data is requested"""
        user = mommy.make(
            "User",
            date_joined=datetime.date(2010, 10, 10),
            is_superuser=True,
            first_name="John",
        )
        mommy.make("User", date_joined=datetime.date(2010, 10, 11), first_name="Karl")
        mommy.make("User", date_joined=datetime.date(2010, 10, 18), first_name="Mark")
        current_tz = timezone.get_current_timezone()
        time_since = datetime.datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime.datetime(2010, 10, 13).astimezone(current_tz)

        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
            choices_based_on_time_range=True,
        )
        serie = self.stats.get_multi_time_series_cached(
            {
                "reload_all": "True",
                "select_box_multiple_series": m2m.id,
            },
            time_since,
            time_until,
            "days",
            None,
            None,
            user,
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 0},
            datetime.datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 0},
            datetime.datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"John": 1, "Karl": 0},
            datetime.datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 1},
            datetime.datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 0},
            datetime.datetime(2010, 10, 13, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 0},
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_cached_dynamic(self):
        """
        Test function to check DashboardStats.get_multi_time_series_cached()
        with m2m criteria with dynamic_choices
        """
        user = mommy.make(
            "User", date_joined=datetime.date(2010, 10, 10), first_name="Milos", is_superuser=True
        )
        mommy.make("User", date_joined=datetime.date(2010, 10, 12), first_name="Milos")
        mommy.make("User", date_joined=datetime.date(2010, 10, 11), first_name="Kuba")
        current_tz = timezone.get_current_timezone()
        time_since = datetime.datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime.datetime(2010, 10, 12).astimezone(current_tz)
        criteria = mommy.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = mommy.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="dynamic_choices",
            choices_based_on_time_range=True,
        )

        interval = "days"
        serie = self.stats.get_multi_time_series_cached(
            {f"select_box_dynamic_{m2m.id}": "Milos"},
            time_since,
            time_until,
            interval,
            None,
            None,
            user,
        )
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime.datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 0},
            datetime.datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 1},
        }
        self.assertDictEqual(serie, testing_data)
