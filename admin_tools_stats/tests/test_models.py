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
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from model_mommy import mommy


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
        self.kid_stats = mommy.make(
            'DashboardStats',
            date_field_name="birthday",
            model_name="TestKid",
            model_app_name="demoproject",
            graph_key="kid_graph",
        )

    def test_clean_error_model_app_app_name(self):
        stats = mommy.make('DashboardStats', model_name="User1", model_app_name="auth1", graph_key="error_graph")
        with self.assertRaisesRegex(ValidationError, "model_name.*No installed app with label"):
            stats.clean()

    def test_clean_error_model_name(self):
        stats = mommy.make('DashboardStats', model_name="User1", model_app_name="auth", graph_key="error_graph")
        with self.assertRaisesRegex(ValidationError, "model_name.*App 'auth' doesn't have a 'User1' model."):
            stats.clean()

    def test_clean_error_operation_field(self):
        stats = mommy.make('DashboardStats', model_name="User", model_app_name="auth", graph_key="error_graph", operation_field_name='asdf')
        with self.assertRaisesRegex(ValidationError, "operation_field_name.*Cannot resolve keyword 'asdf' into field. Choices are:"):
            stats.clean()

    def test_clean_error_date_field(self):
        stats = mommy.make('DashboardStats', model_name="User", model_app_name="auth", graph_key="error_graph", date_field_name='asdf')
        with self.assertRaisesRegex(ValidationError, "date_field_name.*Cannot resolve keyword 'asdf' into field. Choices are:"):
            stats.clean()

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
    @override_settings(USE_TZ=False)
    def test_get_multi_series(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 10))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 10, 12)

        interval = "days"
        serie = self.stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 9, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 10, 0, 0): {'': 1},
            datetime.datetime(2010, 10, 11, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 12, 0, 0): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
    @override_settings(USE_TZ=False)
    def test_get_multi_series_time_based_choices(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Choices are based on time range
        """
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series', choices_based_on_time_range=True)
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 10), first_name="Petr", is_superuser=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 9), first_name="Adam")
        mommy.make('User', date_joined=datetime.date(2010, 10, 15), first_name="Jirka")
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 10, 12)

        interval = "days"
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {'Adam': 0, 'Petr': 0},
            datetime.datetime(2010, 10, 9, 0, 0): {'Adam': 1, 'Petr': 0},
            datetime.datetime(2010, 10, 10, 0, 0): {'Adam': 0, 'Petr': 1},
            datetime.datetime(2010, 10, 11, 0, 0): {'Adam': 0, 'Petr': 0},
            datetime.datetime(2010, 10, 12, 0, 0): {'Adam': 0, 'Petr': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
    @override_settings(USE_TZ=False)
    def test_get_multi_series_count_limit(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Choices are limited by count
        """
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="name",
            dynamic_criteria_field_name="first_name",
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series', count_limit=1)
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 10), first_name="Petr", is_superuser=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 10), first_name="Petr")
        mommy.make('User', date_joined=datetime.date(2010, 10, 9), first_name="Adam")
        mommy.make('User', date_joined=datetime.date(2010, 10, 11), first_name="Jirka")
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 10, 12)

        interval = "days"
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {'other': 0, 'Petr': 0},
            datetime.datetime(2010, 10, 9, 0, 0): {'other': 1, 'Petr': 0},
            datetime.datetime(2010, 10, 10, 0, 0): {'other': 0, 'Petr': 2},
            datetime.datetime(2010, 10, 11, 0, 0): {'other': 1, 'Petr': 0},
            datetime.datetime(2010, 10, 12, 0, 0): {'other': 0, 'Petr': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
    @override_settings(USE_TZ=False)
    def test_get_multi_series_hours(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make('User', date_joined=datetime.datetime(2010, 10, 8, 23, 13))
        time_since = datetime.datetime(2010, 10, 8, 22)
        time_until = datetime.datetime(2010, 10, 8, 23)

        interval = "hours"
        serie = self.stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 8, 22, 0): {'': 0},
            datetime.datetime(2010, 10, 8, 23, 0): {'': 1},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
    @override_settings(USE_TZ=False)
    def test_get_multi_series_weeks(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 30))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 11, 8)

        interval = "weeks"
        serie = self.stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 4, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 11, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 18, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 25, 0, 0): {'': 1},
            datetime.datetime(2010, 11, 1, 0, 0): {'': 0},
            datetime.datetime(2010, 11, 8, 0, 0): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
    @override_settings(USE_TZ=False)
    def test_get_multi_series_months(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 30))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 11, 30)

        interval = "months"
        serie = self.stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 1, 0, 0): {'': 1},
            datetime.datetime(2010, 11, 1, 0, 0): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
    @override_settings(USE_TZ=False)
    def test_get_multi_series_quarters(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 30))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2011, 10, 8)

        interval = "quarters"
        serie = self.stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 1, 0, 0): {'': 1},
            datetime.datetime(2011, 1, 1, 0, 0): {'': 0},
            datetime.datetime(2011, 4, 1, 0, 0): {'': 0},
            datetime.datetime(2011, 7, 1, 0, 0): {'': 0},
            datetime.datetime(2011, 10, 1, 0, 0): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
    @override_settings(USE_TZ=False)
    def test_get_multi_series_years(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 30))
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2011, 10, 8)

        interval = "years"
        serie = self.stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 1, 1, 0, 0): {'': 1},
            datetime.datetime(2011, 1, 1, 0, 0): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE='Europe/Prague')
    def test_get_multi_series_datetime_tz(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        current_tz = timezone.get_current_timezone()
        user = mommy.make('User', date_joined=datetime.datetime(2010, 10, 10, tzinfo=current_tz))
        mommy.make('User', date_joined=datetime.datetime(2010, 10, 10, 12, 34, tzinfo=current_tz))
        time_since = datetime.datetime(2010, 10, 9, 0, 0)
        time_until = datetime.datetime(2010, 10, 11, 0, 0)

        interval = "days"
        serie = self.stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 9, 0, 0).astimezone(current_tz): {'': 0},
            datetime.datetime(2010, 10, 10, 0, 0).astimezone(current_tz): {'': 2},
            datetime.datetime(2010, 10, 11, 0, 0).astimezone(current_tz): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE='CET')
    def test_get_multi_series_date_tz(self):
        """Test function to check DashboardStats.get_multi_time_series()"""
        mommy.make('TestKid', birthday=datetime.date(2010, 10, 10))
        mommy.make('TestKid', birthday=None)
        time_since = datetime.datetime(2010, 10, 9)
        time_until = datetime.datetime(2010, 10, 11)

        interval = "days"
        user = mommy.make('User')
        serie = self.kid_stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.date(2010, 10, 9): {'': 0},
            datetime.date(2010, 10, 10): {'': 1},
            datetime.date(2010, 10, 11): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE='Europe/Prague')
    def test_get_multi_series_change_dst(self):
        """Test function to check DashboardStats.get_multi_time_series() on edge of daylight saving time change """
        current_tz = timezone.get_current_timezone()
        user = mommy.make('User', date_joined=datetime.datetime(2019, 10, 28, tzinfo=current_tz))
        time_since = datetime.datetime(2019, 10, 27, 0, 0)
        time_until = datetime.datetime(2019, 10, 29, 0, 0)

        interval = "days"
        serie = self.stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2019, 10, 27, 0, 0).astimezone(current_tz): {'': 0},
            datetime.datetime(2019, 10, 28, 0, 0).astimezone(current_tz): {'': 1},
            datetime.datetime(2019, 10, 29, 0, 0).astimezone(current_tz): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
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
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 10), first_name="Foo")
        mommy.make('User', date_joined=datetime.date(2010, 10, 10), first_name="Foo")
        mommy.make('User', date_joined=datetime.date(2010, 10, 10), first_name="Bar")
        time_since = datetime.datetime(2010, 10, 8)
        time_until = datetime.datetime(2010, 10, 12)

        interval = "days"
        serie = stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 8, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 9, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 10, 0, 0): {'': 2},
            datetime.datetime(2010, 10, 11, 0, 0): {'': 0},
            datetime.datetime(2010, 10, 12, 0, 0): {'': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
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
            mommy.make('TestKid', birthday=None)
            time_since = datetime.datetime(2010, 10, 9)
            time_until = datetime.datetime(2010, 10, 10)

            interval = "days"
            user = mommy.make('User')
            serie = stats.get_multi_time_series({}, time_since, time_until, interval, None, None, user)
            self.assertEqual(serie[datetime.date(2010, 10, 10)][''], result, "Bad value for function %s" % func)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
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
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 12), is_active=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 13), is_active=False)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Active', 1), ('Inactive', 0))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Active', 0), ('Inactive', 1))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
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
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 12), is_active=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 13), is_active=False)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Active', 1), ('Inactive', 0))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Active', 0), ('Inactive', 1))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Active', 0), ('Inactive', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
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
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 12), is_active=True)
        mommy.make('User', date_joined=datetime.date(2010, 10, 13), is_active=False)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('True', 0), ('False', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('True', 0), ('False', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('True', 1), ('False', 0))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('True', 0), ('False', 1))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('True', 0), ('False', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
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
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        user = mommy.make('User', is_superuser=True)
        serie = self.stats.get_multi_time_series({'select_box_multiple_series': m2m.id}, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Bar', 0), ('Foo', 1))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Bar', 1), ('Foo', 0))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
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
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        user = mommy.make('User', is_superuser=True)
        arguments = {'select_box_multiple_series': m2m.id, 'select_box_dynamic_%s' % m2m_active.id: 'True'}
        serie = self.stats.get_multi_time_series(arguments, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Bar', 0), ('Foo', 1))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_get_multi_series_criteria_combine_user_exception(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        If user has no permission and user field is not defined, exception must be thrown.
        """
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series')
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        user = mommy.make('User')
        arguments = {'select_box_multiple_series': m2m.id}
        with self.assertRaisesRegex(Exception, "^User field must be defined to enable charts for non-superusers$"):
            self.stats.get_multi_time_series(arguments, time_since, time_until, interval, None, None, user)

    @skipIf(django.VERSION[0] < 3, "Django < 3 doesn't support Sum")
    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_get_multi_series_criteria_user(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Check results, if stats are displayed for user
        """
        stats = mommy.make(
            'DashboardStats',
            model_name="TestKid",
            date_field_name='appointment',
            model_app_name="demoproject",
            type_operation_field_name="Sum",
            distinct=True,
            operation_field_name='age',
            user_field_name='author',
        )
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="name",
            dynamic_criteria_field_name="name",
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=stats, use_as='multiple_series')
        user = mommy.make('User')
        mommy.make('TestKid', appointment=datetime.date(2010, 10, 12), name="Foo", age=5, author=user)
        mommy.make('TestKid', appointment=datetime.date(2010, 10, 13), name="Bar", age=7, author=user)
        mommy.make('TestKid', appointment=datetime.date(2010, 10, 13), name="Bar", age=7)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        arguments = {'select_box_multiple_series': m2m.id}
        serie = stats.get_multi_time_series(arguments, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0, tzinfo=datetime.timezone.utc): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 11, 0, 0, tzinfo=datetime.timezone.utc): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 12, 0, 0, tzinfo=datetime.timezone.utc): OrderedDict((('Bar', None), ('Foo', 5))),
            datetime.datetime(2010, 10, 13, 0, 0, tzinfo=datetime.timezone.utc): OrderedDict((('Bar', 7), ('Foo', None))),
            datetime.datetime(2010, 10, 14, 0, 0, tzinfo=datetime.timezone.utc): OrderedDict((('Bar', 0), ('Foo', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(django.VERSION[0] < 3, "Django < 3 doesn't support Avg")
    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_get_multi_series_criteria_isnull(self):
        """
        Test function to check DashboardStats.get_multi_time_series()
        Check __isnull criteria
        """
        stats = mommy.make(
            'DashboardStats',
            model_name="TestKid",
            date_field_name='appointment',
            model_app_name="demoproject",
            type_operation_field_name="Avg",
            distinct=True,
            operation_field_name='age',
        )
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="birthday",
            dynamic_criteria_field_name="birthday__isnull",
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=stats, use_as='multiple_series')
        mommy.make('TestKid', appointment=datetime.date(2010, 10, 12), birthday=datetime.date(2010, 11, 12), age=4)
        mommy.make('TestKid', appointment=datetime.date(2010, 10, 13), birthday=None, age=3)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        arguments = {'select_box_multiple_series': m2m.id}
        user = mommy.make('User', is_staff=True)
        serie = stats.get_multi_time_series(arguments, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0, tzinfo=datetime.timezone.utc): {'Blank': 0, 'Non blank': 0},
            datetime.datetime(2010, 10, 11, 0, 0, tzinfo=datetime.timezone.utc): {'Blank': 0, 'Non blank': 0},
            datetime.datetime(2010, 10, 12, 0, 0, tzinfo=datetime.timezone.utc): {'Blank': None, 'Non blank': 4},
            datetime.datetime(2010, 10, 13, 0, 0, tzinfo=datetime.timezone.utc): {'Blank': 3, 'Non blank': None},
            datetime.datetime(2010, 10, 14, 0, 0, tzinfo=datetime.timezone.utc): {'Blank': 0, 'Non blank': 0},
        }
        self.assertDictEqual(serie, testing_data)

    @skipIf(settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql', 'no support of USE_TZ=False in mysql')
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
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)

        interval = "days"
        arguments = {'select_box_multiple_series': m2m.id}
        user = mommy.make('User', is_superuser=True)
        serie = self.stats.get_multi_time_series(arguments, time_since, time_until, interval, None, None, user)
        testing_data = {
            datetime.datetime(2010, 10, 10, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 11, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 12, 0, 0): OrderedDict((('Bar', 0), ('Foo', 1))),
            datetime.datetime(2010, 10, 13, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
            datetime.datetime(2010, 10, 14, 0, 0): OrderedDict((('Bar', 0), ('Foo', 0))),
        }
        self.assertDictEqual(serie, testing_data)

    def test_no_user_field_name(self):
        """
        Test that non-superuser without user_field_name can't see charts
        """
        criteria = mommy.make(
            'DashboardStatsCriteria',
            criteria_name="name",
            dynamic_criteria_field_name="last_name",
        )
        mommy.make(
            'DashboardStatsCriteria',
            criteria_name="active",
            criteria_fix_mapping={"is_active": True},
        )
        m2m = mommy.make('CriteriaToStatsM2M', criteria=criteria, stats=self.stats, use_as='multiple_series')
        user = mommy.make('User', date_joined=datetime.date(2010, 10, 12), last_name="Foo", is_active=True)
        time_since = datetime.datetime(2010, 10, 10)
        time_until = datetime.datetime(2010, 10, 14)
        arguments = {'select_box_multiple_series': m2m.id}
        with self.assertRaises(Exception):
            self.stats.get_multi_time_series(arguments, time_since, time_until, "days", None, user)
