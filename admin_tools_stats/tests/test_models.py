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
from collections import OrderedDict
from datetime import date, datetime, timezone
from unittest import skipIf

import django
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.aggregates import Avg, Count, Max, Min, StdDev, Sum, Variance
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone as dj_timezone
from model_bakery import baker

from admin_tools_stats.models import CachedValue, Interval, truncate_ceiling


try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo  # type: ignore

UTC = timezone.utc
chicago_tz = zoneinfo.ZoneInfo(key="America/Chicago")


class DashboardStatsCriteriaTests(TestCase):
    def test_criteria_dynamic_mapping_preview(self):
        """
        Test criteria_dynamic_mapping_preview() function
        """
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            criteria_dynamic_mapping="{'foo': 'bar'}",
        )
        self.assertEqual(criteria.criteria_dynamic_mapping_preview(), "{'foo': 'bar'}")

    def test_criteria_dynamic_mapping_preview_blank(self):
        """
        Test criteria_dynamic_mapping_preview() function
        """
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
        )
        self.assertEqual(criteria.criteria_dynamic_mapping_preview(), "")

    def test_criteria_dynamic_mapping_preview_long(self):
        """
        Test criteria_dynamic_mapping_preview() function
        """
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            criteria_dynamic_mapping="{'foo': 'bar" + "a" * 105 + "'}",
        )
        result = criteria.criteria_dynamic_mapping_preview()
        self.assertTrue("{'foo': 'baraaaaaa" in result)
        self.assertTrue("aaaaaa..." in result)
        self.assertEqual(len(result), 103)

    def test_criteria_m2m_get_dynamic_criteria_field_name_prefix(self):
        """
        Test get_dynamic_criteria_field_name() function
        """
        criteria = baker.make(
            "CriteriaToStatsM2M",
            criteria__dynamic_criteria_field_name="field_name",
            prefix="related__",
        )
        result = criteria.get_dynamic_criteria_field_name()
        self.assertEqual(result, "related__field_name")

    def test__get_dynamic_choices_no_field_name(self):
        """
        Test _get_dynamic_choices() function
        """
        criteria_m2m = baker.make(
            "CriteriaToStatsM2M",
            stats__graph_title="Graph",
            criteria__criteria_name="Foo",
            criteria__dynamic_criteria_field_name="",
            stats__model_app_name="auth",
            stats__model_name="User",
            stats__cache_values=False,
        )
        result = criteria_m2m._get_dynamic_choices(None, None)
        self.assertEqual(result, None)

    def test__get_dynamic_choices_time_values(self):
        """
        Test _get_dynamic_choices() function
        """
        baker.make("User", first_name="user1", last_name="bar_1", date_joined=date(2014, 1, 1))
        criteria_m2m = baker.make(
            "CriteriaToStatsM2M",
            stats__graph_title="Graph",
            criteria__criteria_name="Foo",
            criteria__dynamic_criteria_field_name="first_name",
            stats__model_app_name="auth",
            stats__model_name="User",
            stats__cache_values=False,
            stats__date_field_name="date_joined",
        )
        result = criteria_m2m._get_dynamic_choices(
            datetime(2014, 1, 1, tzinfo=UTC), datetime(2014, 1, 2, tzinfo=UTC)
        )
        self.assertEqual(result, OrderedDict([("user1", ("user1", "user1"))]))
        result = criteria_m2m._get_dynamic_choices(
            datetime(2014, 1, 1, tzinfo=None), datetime(2014, 1, 2, tzinfo=None)
        )
        self.assertEqual(result, OrderedDict([("user1", ("user1", "user1"))]))

    def test__get_dynamic_choices_caching(self):
        """
        Test _get_dynamic_choices() function

        Test, that the value is really cached, but invalidates after CriteriaToStatsM2M save

        Different criteria should have different value
        This didn't work with cache_utils, and had to be
        dealt with slef parameter containing another self
        """
        baker.make("User", first_name="user1", last_name="bar_1")
        criteria_m2m = baker.make(
            "CriteriaToStatsM2M",
            stats__graph_title="Graph",
            criteria__criteria_name="Foo",
            criteria__dynamic_criteria_field_name="first_name",
            stats__model_app_name="auth",
            stats__model_name="User",
            stats__cache_values=False,
        )
        self.assertEqual(
            criteria_m2m._get_dynamic_choices(None, None),
            OrderedDict([("user1", ("user1", "user1"))]),
        )

        criteria_m2m_1 = baker.make(
            "CriteriaToStatsM2M",
            criteria__dynamic_criteria_field_name="last_name",
            stats__model_app_name="auth",
            stats__model_name="User",
        )
        self.assertEqual(
            criteria_m2m_1._get_dynamic_choices(None, None),
            OrderedDict([("bar_1", ("bar_1", "bar_1"))]),
        )

        user2 = baker.make("User", first_name="user2", last_name="bar_2")
        self.assertEqual(  # Value is cached, so it doesn't change
            criteria_m2m._get_dynamic_choices(None, None),
            OrderedDict([("user1", ("user1", "user1"))]),
        )

        criteria_m2m.criteria.save()
        self.assertEqual(  # Criteria save invalidates cache, so returned value changes
            criteria_m2m._get_dynamic_choices(None, None),
            OrderedDict([("user1", ("user1", "user1")), ("user2", ("user2", "user2"))]),
        )

        user2.first_name = "user3"
        user2.save()
        self.assertEqual(  # Cache is not invalidated, so returned value doesn't change
            criteria_m2m._get_dynamic_choices(None, None),
            OrderedDict([("user1", ("user1", "user1")), ("user2", ("user2", "user2"))]),
        )

        criteria_m2m.save()
        self.assertEqual(  # Criteria save invalidates cache, so returned value changes
            criteria_m2m._get_dynamic_choices(None, None),
            OrderedDict([("user1", ("user1", "user1")), ("user3", ("user3", "user3"))]),
        )

        user2.first_name = "user4"
        user2.save()
        self.assertEqual(  # Cache is not invalidated, so returned value doesn't change
            criteria_m2m._get_dynamic_choices(None, None),
            OrderedDict([("user1", ("user1", "user1")), ("user3", ("user3", "user3"))]),
        )

        criteria_m2m.stats.save()
        self.assertEqual(  # Criteria save invalidates cache, so returned value changes
            criteria_m2m._get_dynamic_choices(None, None),
            OrderedDict([("user1", ("user1", "user1")), ("user4", ("user4", "user4"))]),
        )

        # Value for different criteria didn't invalidate the whole time
        self.assertEqual(
            criteria_m2m_1._get_dynamic_choices(None, None),
            OrderedDict([("bar_1", ("bar_1", "bar_1"))]),
        )

        # But now they will
        criteria_m2m_1.save()
        self.assertEqual(
            criteria_m2m_1._get_dynamic_choices(None, None),
            OrderedDict([("bar_1", ("bar_1", "bar_1")), ("bar_2", ("bar_2", "bar_2"))]),
        )


class ModelTests(TestCase):
    maxDiff = None

    def setUp(self):
        self.stats = baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
        )
        self.kid_stats = baker.make(
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
        stats = baker.make(
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
        stats = baker.make(
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
        stats = baker.make(
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
        user = baker.make("User", date_joined=date(2010, 10, 10))
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2010, 10, 12)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 8, 0, 0): {"": 0},
            datetime(2010, 10, 9, 0, 0): {"": 0},
            datetime(2010, 10, 10, 0, 0): {"": 1},
            datetime(2010, 10, 11, 0, 0): {"": 0},
            datetime(2010, 10, 12, 0, 0): {"": 0},
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
        user = baker.make("User", first_name="Milos", is_superuser=True)
        baker.make("TestKid", author=user, birthday=date(2010, 10, 10))
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2010, 10, 12)
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.kid_stats,
            prefix="author__",
            use_as="multiple_series",
            choices_based_on_time_range=True,
        )

        serie = self.kid_stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            date(2010, 10, 8): {"Milos": 0},
            date(2010, 10, 9): {"Milos": 0},
            date(2010, 10, 10): {"Milos": 1},
            date(2010, 10, 11): {"Milos": 0},
            date(2010, 10, 12): {"Milos": 0},
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
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
            choices_based_on_time_range=True,
        )
        user = baker.make(
            "User",
            date_joined=date(2010, 10, 10),
            first_name="Petr",
            is_superuser=True,
        )
        baker.make("User", date_joined=date(2010, 10, 9), first_name="Adam")
        baker.make("User", date_joined=date(2010, 10, 15), first_name="Jirka")
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2010, 10, 12)

        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            datetime(2010, 10, 8, 0, 0): {"Adam": 0, "Petr": 0},
            datetime(2010, 10, 9, 0, 0): {"Adam": 1, "Petr": 0},
            datetime(2010, 10, 10, 0, 0): {"Adam": 0, "Petr": 1},
            datetime(2010, 10, 11, 0, 0): {"Adam": 0, "Petr": 0},
            datetime(2010, 10, 12, 0, 0): {"Adam": 0, "Petr": 0},
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
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
            count_limit=1,
        )
        user = baker.make(
            "User",
            date_joined=date(2010, 10, 10),
            first_name="Petr",
            is_superuser=True,
        )
        baker.make("User", date_joined=date(2010, 10, 10), first_name="Petr")
        baker.make("User", date_joined=date(2010, 10, 9), first_name="Adam")
        baker.make("User", date_joined=date(2010, 10, 11), first_name="Jirka")
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2010, 10, 12)

        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            datetime(2010, 10, 8, 0, 0): {"other": 0, "Petr": 0},
            datetime(2010, 10, 9, 0, 0): {"other": 1, "Petr": 0},
            datetime(2010, 10, 10, 0, 0): {"other": 0, "Petr": 2},
            datetime(2010, 10, 11, 0, 0): {"other": 1, "Petr": 0},
            datetime(2010, 10, 12, 0, 0): {"other": 0, "Petr": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_hours(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = baker.make("User", date_joined=datetime(2010, 10, 8, 23, 13))
        time_since = datetime(2010, 10, 8, 22)
        time_until = datetime(2010, 10, 8, 23, 59)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.hours, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 8, 22, 0): {"": 0},
            datetime(2010, 10, 8, 23, 0): {"": 1},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_weeks(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = baker.make("User", date_joined=date(2010, 10, 30))
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2010, 11, 8)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.weeks, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 4, 0, 0): {"": 0},
            datetime(2010, 10, 11, 0, 0): {"": 0},
            datetime(2010, 10, 18, 0, 0): {"": 0},
            datetime(2010, 10, 25, 0, 0): {"": 1},
            datetime(2010, 11, 1, 0, 0): {"": 0},
            datetime(2010, 11, 8, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_months(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = baker.make("User", date_joined=date(2010, 10, 30))
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2010, 11, 30)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.months, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 1, 0, 0): {"": 1},
            datetime(2010, 11, 1, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_quarters(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = baker.make("User", date_joined=date(2010, 10, 30))
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2011, 10, 8)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.quarters, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 1, 0, 0): {"": 1},
            datetime(2011, 1, 1, 0, 0): {"": 0},
            datetime(2011, 4, 1, 0, 0): {"": 0},
            datetime(2011, 7, 1, 0, 0): {"": 0},
            datetime(2011, 10, 1, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_years(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = baker.make("User", date_joined=date(2010, 10, 30))
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2011, 10, 8)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.years, None, None, user
        )
        testing_data = {
            datetime(2010, 1, 1, 0, 0): {"": 1},
            datetime(2011, 1, 1, 0, 0): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="Europe/Prague")
    def test_get_multi_series_datetime_tz(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        current_tz = dj_timezone.get_current_timezone()
        user = baker.make("User", date_joined=datetime(2010, 10, 10, tzinfo=current_tz))
        baker.make("User", date_joined=datetime(2010, 10, 10, 12, 34, tzinfo=current_tz))
        time_since = datetime(2010, 10, 9, 0, 0)
        time_until = datetime(2010, 10, 11, 0, 0)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 2},
            datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="Europe/Prague", ADMIN_CHARTS_TIMEZONE="UTC")
    def test_get_multi_series_datetime_set_utc(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Test, that everything works, if the chart is set in different timezone than the server
        """
        current_tz = dj_timezone.get_current_timezone()
        user = baker.make("User", date_joined=datetime(2010, 10, 10, 0, 0, tzinfo=current_tz))
        baker.make("User", date_joined=datetime(2010, 10, 10, 23, 34, tzinfo=current_tz))
        baker.make("User", date_joined=datetime(2010, 10, 10, 23, 34, tzinfo=UTC))
        time_since = datetime(2010, 10, 9, 0, 0, tzinfo=UTC)
        time_until = datetime(2010, 10, 11, 0, 0, tzinfo=UTC)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 9, 0, 0, tzinfo=UTC): {"": 1},
            datetime(2010, 10, 10, 0, 0, tzinfo=UTC): {"": 2},
            datetime(2010, 10, 11, 0, 0, tzinfo=UTC): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="Europe/Prague", ADMIN_CHARTS_TIMEZONE=UTC)
    def test_get_multi_series_datetime_set_utc_zone(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Test, that everything works, if the chart is set in different timezone than the server
        Set timezone by zone parameter
        """
        current_tz = dj_timezone.get_current_timezone()
        user = baker.make("User", date_joined=datetime(2010, 10, 10, 0, 0, tzinfo=current_tz))
        baker.make("User", date_joined=datetime(2010, 10, 10, 23, 34, tzinfo=current_tz))
        baker.make("User", date_joined=datetime(2010, 10, 10, 23, 34, tzinfo=UTC))
        time_since = datetime(2010, 10, 9, 0, 0, tzinfo=UTC)
        time_until = datetime(2010, 10, 11, 0, 0, tzinfo=UTC)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 9, 0, 0, tzinfo=UTC): {"": 1},
            datetime(2010, 10, 10, 0, 0, tzinfo=UTC): {"": 2},
            datetime(2010, 10, 11, 0, 0, tzinfo=UTC): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="CET")
    def test_get_multi_series_date_tz(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        baker.make("TestKid", birthday=date(2010, 10, 10))
        baker.make("TestKid", birthday=None)
        time_since = datetime(2010, 10, 9)
        time_until = datetime(2010, 10, 11)

        user = baker.make("User")
        serie = self.kid_stats.get_multi_time_series(
            {}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            date(2010, 10, 9): {"": 0},
            date(2010, 10, 10): {"": 1},
            date(2010, 10, 11): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="Europe/Prague")
    def test_get_multi_series_change_dst(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        on edge of daylight saving time change
        """
        current_tz = zoneinfo.ZoneInfo("Europe/Prague")
        user = baker.make("User", date_joined=datetime(2019, 10, 28).astimezone(current_tz))
        time_since = datetime(2019, 10, 27, 0, 0)
        time_until = datetime(2019, 10, 29, 0, 0)

        serie = self.stats.get_multi_time_series(
            {}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2019, 10, 27, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2019, 10, 28, 0, 0).astimezone(current_tz): {"": 1},
            datetime(2019, 10, 29, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(
        settings.DATABASES["default"]["ENGINE"] == "django.db.backends.mysql",
        "no support of USE_TZ=False in mysql",
    )
    @override_settings(USE_TZ=False)
    def test_get_multi_series_distinct_count(self):
        """Test function to check DashboardStats.get_multi_time_series() with distinct count."""
        stats = baker.make(
            "DashboardStats",
            model_name="User",
            date_field_name="date_joined",
            model_app_name="auth",
            type_operation_field_name="Count",
            distinct=True,
            operation_field_name="first_name",
        )
        user = baker.make("User", date_joined=date(2010, 10, 10), first_name="Foo")
        baker.make("User", date_joined=date(2010, 10, 10), first_name="Foo")
        baker.make("User", date_joined=date(2010, 10, 10), first_name="Bar")
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2010, 10, 12)

        serie = stats.get_multi_time_series(
            {}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 8, 0, 0): {"": 0},
            datetime(2010, 10, 9, 0, 0): {"": 0},
            datetime(2010, 10, 10, 0, 0): {"": 2},
            datetime(2010, 10, 11, 0, 0): {"": 0},
            datetime(2010, 10, 12, 0, 0): {"": 0},
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
            stats = baker.make(
                "DashboardStats",
                model_name="TestKid",
                date_field_name="birthday",
                model_app_name="demoproject",
                type_operation_field_name=func,
                operation_field_name="age",
            )
            baker.make("TestKid", birthday=date(2010, 10, 10), age=12)
            baker.make("TestKid", birthday=date(2010, 10, 10), age=1)
            baker.make("TestKid", birthday=date(2010, 10, 10), age=2)
            baker.make("TestKid", birthday=None)
            time_since = datetime(2010, 10, 9)
            time_until = datetime(2010, 10, 10)

            user = baker.make("User")
            serie = stats.get_multi_time_series(
                {}, time_since, time_until, Interval.days, None, None, user
            )
            self.assertEqual(
                serie[date(2010, 10, 10)][""],
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
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        user = baker.make("User", date_joined=date(2010, 10, 12), is_active=True)
        baker.make("User", date_joined=date(2010, 10, 13), is_active=False)
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
            datetime(2010, 10, 11, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
            datetime(2010, 10, 12, 0, 0): OrderedDict((("Active", 1), ("Inactive", 0))),
            datetime(2010, 10, 13, 0, 0): OrderedDict((("Active", 0), ("Inactive", 1))),
            datetime(2010, 10, 14, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
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
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
            criteria_dynamic_mapping={
                "False": "Inactive",
                "True": "Active",
            },
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        user = baker.make("User", date_joined=date(2010, 10, 12), is_active=True)
        baker.make("User", date_joined=date(2010, 10, 13), is_active=False)
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
            datetime(2010, 10, 11, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
            datetime(2010, 10, 12, 0, 0): OrderedDict((("Active", 1), ("Inactive", 0))),
            datetime(2010, 10, 13, 0, 0): OrderedDict((("Active", 0), ("Inactive", 1))),
            datetime(2010, 10, 14, 0, 0): OrderedDict((("Active", 0), ("Inactive", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_criteria_time_exception(self):
        """
        Test exception is thrown, if time_since is greate than time_until
        """
        user = baker.make("User", date_joined=date(2010, 10, 12), is_active=True)
        with self.assertRaisesRegex(Exception, "time_since is greater than time_until"):
            self.stats.get_multi_time_series(
                {}, datetime(2010, 10, 14), datetime(2010, 10, 10), "days", None, None, user
            )

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
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        user = baker.make("User", date_joined=date(2010, 10, 12), is_active=True)
        baker.make("User", date_joined=date(2010, 10, 13), is_active=False)
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0): OrderedDict((("True", 0), ("False", 0))),
            datetime(2010, 10, 11, 0, 0): OrderedDict((("True", 0), ("False", 0))),
            datetime(2010, 10, 12, 0, 0): OrderedDict((("True", 1), ("False", 0))),
            datetime(2010, 10, 13, 0, 0): OrderedDict((("True", 0), ("False", 1))),
            datetime(2010, 10, 14, 0, 0): OrderedDict((("True", 0), ("False", 0))),
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
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        baker.make("User", date_joined=date(2010, 10, 12), last_name="Foo")
        baker.make("User", date_joined=date(2010, 10, 13), last_name="Bar")
        baker.make("User", date_joined=date(2010, 10, 14))
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        user = baker.make("User", is_superuser=True)
        serie = self.stats.get_multi_time_series(
            {"select_box_multiple_series": m2m.id},
            time_since,
            time_until,
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 11, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 12, 0, 0): OrderedDict((("Bar", 0), ("Foo", 1))),
            datetime(2010, 10, 13, 0, 0): OrderedDict((("Bar", 1), ("Foo", 0))),
            datetime(2010, 10, 14, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
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
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        criteria_active = baker.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            dynamic_criteria_field_name="is_active",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        m2m_active = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria_active,
            stats=self.stats,
            use_as="chart_filter",
        )
        baker.make(
            "User",
            date_joined=date(2010, 10, 12),
            last_name="Foo",
            is_active=True,
        )
        baker.make(
            "User",
            date_joined=date(2010, 10, 13),
            last_name="Bar",
            is_active=False,
        )
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        user = baker.make("User", is_superuser=True)
        arguments = {
            "select_box_multiple_series": m2m.id,
            "select_box_dynamic_%s" % m2m_active.id: "True",
        }
        serie = self.stats.get_multi_time_series(
            arguments, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 11, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 12, 0, 0): OrderedDict((("Bar", 0), ("Foo", 1))),
            datetime(2010, 10, 13, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 14, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_criteria_combine_user_exception(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        If user has no permission and user field is not defined, exception must be thrown.
        """
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        user = baker.make("User")
        arguments = {"select_box_multiple_series": m2m.id}
        with self.assertRaisesRegex(
            Exception,
            "^User field must be defined to enable charts for non-superusers$",
        ):
            self.stats.get_multi_time_series(
                arguments, time_since, time_until, Interval.days, None, None, user
            )

    @skipIf(django.VERSION[0] < 3, "Django < 3 doesn't support Sum")
    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_criteria_user(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Check results, if stats are displayed for user
        """
        stats = baker.make(
            "DashboardStats",
            model_name="TestKid",
            date_field_name="appointment",
            model_app_name="demoproject",
            type_operation_field_name="Sum",
            distinct=True,
            operation_field_name="age",
            user_field_name="author",
        )
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="name",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=stats,
            use_as="multiple_series",
        )
        user = baker.make("User")
        baker.make(
            "TestKid",
            appointment=date(2010, 10, 12),
            name="Foo",
            age=5,
            author=user,
        )
        baker.make(
            "TestKid",
            appointment=date(2010, 10, 13),
            name="Bar",
            age=7,
            author=user,
        )
        baker.make("TestKid", appointment=date(2010, 10, 13), name="Bar", age=7)
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        arguments = {"select_box_multiple_series": m2m.id}
        serie = stats.get_multi_time_series(
            arguments, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0, tzinfo=UTC): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 11, 0, 0, tzinfo=UTC): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 12, 0, 0, tzinfo=UTC): OrderedDict((("Bar", None), ("Foo", 5))),
            datetime(2010, 10, 13, 0, 0, tzinfo=UTC): OrderedDict((("Bar", 7), ("Foo", None))),
            datetime(2010, 10, 14, 0, 0, tzinfo=UTC): OrderedDict((("Bar", 0), ("Foo", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(django.VERSION[0] < 3, "Django < 3 doesn't support distinct Avg")
    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_criteria_isnull(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Check __isnull criteria
        """
        stats = baker.make(
            "DashboardStats",
            model_name="TestKid",
            date_field_name="appointment",
            model_app_name="demoproject",
            type_operation_field_name="Avg",
            distinct=True,
            operation_field_name="age",
        )
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="birthday",
            dynamic_criteria_field_name="birthday__isnull",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=stats,
            use_as="multiple_series",
        )
        baker.make(
            "TestKid",
            appointment=date(2010, 10, 12),
            birthday=date(2010, 11, 12),
            age=4,
        )
        baker.make("TestKid", appointment=date(2010, 10, 13), birthday=None, age=3)
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        arguments = {"select_box_multiple_series": m2m.id}
        user = baker.make("User", is_staff=True)
        serie = stats.get_multi_time_series(
            arguments, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0, tzinfo=UTC): {"Blank": 0, "Non blank": 0},
            datetime(2010, 10, 11, 0, 0, tzinfo=UTC): {"Blank": 0, "Non blank": 0},
            datetime(2010, 10, 12, 0, 0, tzinfo=UTC): {"Blank": None, "Non blank": 4},
            datetime(2010, 10, 13, 0, 0, tzinfo=UTC): {"Blank": 3, "Non blank": None},
            datetime(2010, 10, 14, 0, 0, tzinfo=UTC): {"Blank": 0, "Non blank": 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE="UTC")
    def test_get_multi_series_criteria_multiple_operations(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Test case with multiple operations and no operation field set
        """
        stats = baker.make(
            "DashboardStats",
            model_name="TestKid",
            date_field_name="appointment",
            model_app_name="demoproject",
            type_operation_field_name="Sum",
            operation_field_name="age, height",
        )
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="birthday",
            dynamic_criteria_field_name="birthday__isnull",
        )
        baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=stats,
            use_as="multiple_series",
        )
        baker.make(
            "TestKid",
            appointment=date(2010, 10, 12),
            birthday=date(2010, 11, 12),
            age=4,
            height=60,
        )
        baker.make("TestKid", appointment=date(2010, 10, 13), birthday=None, age=3, height=50)
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        arguments = {"operation_choice": ""}
        user = baker.make("User", is_staff=True)
        serie = stats.get_multi_time_series(
            arguments, time_since, time_until, Interval.days, "", None, user
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0, tzinfo=UTC): {"age": 0, "height": 0},
            datetime(2010, 10, 11, 0, 0, tzinfo=UTC): {"age": 0, "height": 0},
            datetime(2010, 10, 12, 0, 0, tzinfo=UTC): {"age": 4, "height": 60},
            datetime(2010, 10, 13, 0, 0, tzinfo=UTC): {"age": 3, "height": 50},
            datetime(2010, 10, 14, 0, 0, tzinfo=UTC): {"age": 0, "height": 0},
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
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        criteria_active = baker.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            criteria_fix_mapping={"is_active": True},
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria_active,
            stats=self.stats,
            use_as="chart_filter",
        )
        baker.make(
            "User",
            date_joined=date(2010, 10, 12),
            last_name="Foo",
            is_active=True,
        )
        baker.make(
            "User",
            date_joined=date(2010, 10, 13),
            last_name="Bar",
            is_active=False,
        )
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)

        arguments = {"select_box_multiple_series": m2m.id}
        user = baker.make("User", is_superuser=True)
        serie = self.stats.get_multi_time_series(
            arguments, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 11, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 12, 0, 0): OrderedDict((("Bar", 0), ("Foo", 1))),
            datetime(2010, 10, 13, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
            datetime(2010, 10, 14, 0, 0): OrderedDict((("Bar", 0), ("Foo", 0))),
        }
        self.assertDictEqual(serie, testing_data)

    def test_no_user_field_name(self):
        """
        Test that non-superuser without user_field_name can't see charts
        """
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        baker.make(
            "DashboardStatsCriteria",
            criteria_name="active",
            criteria_fix_mapping={"is_active": True},
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="multiple_series",
        )
        user = baker.make(
            "User",
            date_joined=date(2010, 10, 12),
            last_name="Foo",
            is_active=True,
        )
        time_since = datetime(2010, 10, 10)
        time_until = datetime(2010, 10, 14)
        arguments = {"select_box_multiple_series": m2m.id}
        with self.assertRaises(Exception):
            self.stats.get_multi_time_series(
                arguments, time_since, time_until, Interval.days, None, user
            )

    def test_truncate_ceiling(self):
        """Test truncate_ceiling() function"""
        date = datetime(2022, 1, 8, 0, 0, tzinfo=chicago_tz)
        self.assertEqual(
            truncate_ceiling(date, "hour"),
            datetime(2022, 1, 8, 0, 59, 59, 999999, tzinfo=chicago_tz),
        )
        self.assertEqual(
            truncate_ceiling(date, "day"),
            datetime(2022, 1, 8, 23, 59, 59, 999999, tzinfo=chicago_tz),
        )
        self.assertEqual(
            truncate_ceiling(date, "week"),
            datetime(2022, 1, 9, 23, 59, 59, 999999, tzinfo=chicago_tz),
        )
        self.assertEqual(
            truncate_ceiling(date, "month"),
            datetime(2022, 1, 31, 23, 59, 59, 999999, tzinfo=chicago_tz),
        )
        self.assertEqual(
            truncate_ceiling(date, "quarter"),
            datetime(2022, 3, 31, 23, 59, 59, 999999, tzinfo=chicago_tz),
        )
        self.assertEqual(
            truncate_ceiling(date, "year"),
            datetime(2022, 12, 31, 23, 59, 59, 999999, tzinfo=chicago_tz),
        )


class GetTimeSeriesTests(TestCase):
    def setUp(self):
        self.stats = baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
        )

    def test_get_time_series(self):
        """Simple test of DashboardStats.get_multi_time_series_cached() same as the variant without cache"""
        user = baker.make("User", date_joined=date(2010, 10, 10))
        CachedValue.objects.all().delete()
        time_since = datetime(2010, 10, 8)
        time_until = datetime(2010, 10, 12)

        serie = self.stats.get_time_series(
            {}, [], user, time_since, time_until, None, None, Interval.days
        )
        testing_data = [
            (datetime(2010, 10, 10, 0, 0).astimezone(UTC), 1),
        ]
        self.assertQuerysetEqual(serie, testing_data)


class CacheModelTests(TestCase):
    maxDiff = None

    def setUp(self):
        self.stats = baker.make(
            "DashboardStats",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            cache_values=True,
        )
        common_parameters = {
            "stats": self.stats,
            "time_scale": "days",
            "operation": None,
            "dynamic_choices": [],
            "filtered_value": "",
        }
        current_tz = dj_timezone.get_current_timezone()
        baker.make(
            "CachedValue",
            **common_parameters,
            date=datetime(2010, 10, 9).astimezone(current_tz),
            value=3,
        )
        baker.make(
            "CachedValue",
            **common_parameters,
            date=datetime(2010, 10, 11).astimezone(current_tz),
            value=5,
        )
        baker.make(
            "CachedValue",
            **common_parameters,
            date=datetime(2010, 10, 12).astimezone(current_tz),
            is_final=False,
            value=5,
        )

    def test_get_multi_series_cached(self):
        """Test DashboardStats.get_multi_time_series_cached() if some values were already in cache"""
        user = baker.make("User", date_joined=date(2010, 10, 10))
        current_tz = dj_timezone.get_current_timezone()
        time_since = datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime(2010, 10, 13).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 3},
            datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 5},
            datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 5},
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_cached_reload(self):
        """
        Simple test of DashboardStats.get_multi_time_series_cached() same as the variant without cache
        Without reload, and with no cached values, the output is blank.
        """
        user = baker.make("User", date_joined=date(2010, 10, 10))
        CachedValue.objects.all().delete()
        current_tz = dj_timezone.get_current_timezone()
        time_since = datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime(2010, 10, 12).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {}
        self.assertDictEqual(serie, testing_data)

    def test_get_gaps(self):
        """Test DashboardStats.get_gaps() if some values were already in cache"""
        current_tz = dj_timezone.get_current_timezone()
        time_since = datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime(2010, 10, 13).astimezone(current_tz)

        gaps = self.stats.get_gaps(
            False, False, time_since, time_until, Interval.days, CachedValue.objects.all()
        )
        expected_gaps = [
            [
                datetime(2010, 10, 8, 0, 0, tzinfo=chicago_tz),
                datetime(2010, 10, 8, 23, 59, 59, 999999, tzinfo=chicago_tz),
            ],
            [
                datetime(2010, 10, 10, 0, 0, tzinfo=chicago_tz),
                datetime(2010, 10, 10, 23, 59, 59, 999999, tzinfo=chicago_tz),
            ],
            [
                datetime(2010, 10, 13, 0, 0, tzinfo=chicago_tz),
                datetime(2010, 10, 13, 23, 59, 59, 999999, tzinfo=chicago_tz),
            ],
        ]
        self.assertEqual(gaps, expected_gaps)

    def test_get_multi_series_cached_values(self):
        """Test DashboardStats.get_multi_time_series_cached() if some values were already in cache"""
        user = baker.make("User", date_joined=date(2010, 10, 10))
        current_tz = dj_timezone.get_current_timezone()
        time_since = datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime(2010, 10, 13).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {"reload": "True"}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 3},
            datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 5},
            datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 13, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_cached_values_reload(self):
        """Same as test above, but the data reload is requested"""
        user = baker.make("User", date_joined=date(2010, 10, 10))
        current_tz = dj_timezone.get_current_timezone()
        time_since = datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime(2010, 10, 13).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {"reload": "True"}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 3},
            datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 5},
            datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 13, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_cached_values_reload_all(self):
        """Same as test above, but reload of all data is requested"""
        user = baker.make("User", date_joined=date(2010, 10, 10))
        current_tz = dj_timezone.get_current_timezone()
        time_since = datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime(2010, 10, 13).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {"reload_all": "True"}, time_since, time_until, Interval.days, None, None, user
        )
        testing_data = {
            datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 13, 0, 0).astimezone(current_tz): {"": 0},
        }
        self.assertDictEqual(serie, testing_data)

    def test_choices_based_on_time_range(self):
        """Same as test above, but reload of all data is requested"""
        user = baker.make(
            "User",
            date_joined=date(2010, 10, 10),
            is_superuser=True,
            first_name="John",
        )
        baker.make("User", date_joined=date(2010, 10, 11), first_name="Karl")
        baker.make("User", date_joined=date(2010, 10, 18), first_name="Mark")
        current_tz = dj_timezone.get_current_timezone()
        time_since = datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime(2010, 10, 13).astimezone(current_tz)

        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = baker.make(
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
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 0},
            datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 0},
            datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"John": 1, "Karl": 0},
            datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 1},
            datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 0},
            datetime(2010, 10, 13, 0, 0).astimezone(current_tz): {"John": 0, "Karl": 0},
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_cached_dynamic(self):
        """
        Test function to check DashboardStats.get_multi_time_series_cached()
        with m2m criteria with dynamic_choices
        """
        user = baker.make(
            "User", date_joined=date(2010, 10, 10), first_name="Milos", is_superuser=True
        )
        baker.make("User", date_joined=date(2010, 10, 12), first_name="Milos")
        baker.make("User", date_joined=date(2010, 10, 11), first_name="Kuba")
        current_tz = dj_timezone.get_current_timezone()
        time_since = datetime(2010, 10, 8).astimezone(current_tz)
        time_until = datetime(2010, 10, 12).astimezone(current_tz)
        criteria = baker.make(
            "DashboardStatsCriteria",
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = baker.make(
            "CriteriaToStatsM2M",
            criteria=criteria,
            stats=self.stats,
            use_as="dynamic_choices",
            choices_based_on_time_range=True,
        )

        serie = self.stats.get_multi_time_series_cached(
            {f"select_box_dynamic_{m2m.id}": "Milos", "reload": "True"},
            time_since,
            time_until,
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            datetime(2010, 10, 8, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 0},
            datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 1},
        }
        self.assertDictEqual(serie, testing_data)

    def test_get_multi_series_cached_last_value(self):
        """
        Test function to check DashboardStats.get_multi_time_series_cached()
        Test, that last value is counted correctly
        """
        CachedValue.objects.all().delete()
        user = baker.make("User", date_joined=date(2010, 10, 10), is_superuser=True)
        baker.make("User", date_joined=datetime(2010, 10, 12, 12, 12))
        baker.make("User", date_joined=datetime(2010, 10, 11))
        current_tz = dj_timezone.get_current_timezone()
        time_since = datetime(2010, 10, 10).astimezone(current_tz)
        time_until = datetime(2010, 10, 12, 23, 59).astimezone(current_tz)

        serie = self.stats.get_multi_time_series_cached(
            {"reload_all": "True"},
            time_since,
            time_until,
            Interval.days,
            None,
            None,
            user,
        )
        testing_data = {
            datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {"": 1},
            datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {"": 1},
            datetime(2010, 10, 12, 0, 0).astimezone(current_tz): {"": 1},
        }
        self.assertDictEqual(serie, testing_data)
