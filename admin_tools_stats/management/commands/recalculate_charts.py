from datetime import datetime, timedelta

from blenderhub.apps.accounts.models import UserProfile
from datetime_truncate import truncate
from django.core.management import BaseCommand

from admin_tools_stats.models import (
    DashboardStats,
    Interval,
    get_charts_timezone,
    truncate_ceiling,
)


class Command(BaseCommand):
    help = "Recalculate all charts with cached values"

    def add_arguments(self, parser):
        parser.add_argument(
            "graph_key",
            nargs="*",
            type=str,
            help="Recalculate only specified charts",
        )
        parser.add_argument(
            "--exclude",
            help="Exclude graph keys from recalculation separated by comma",
        )
        parser.add_argument(
            "--all-criteria",
            help="Run for all multiseries criteria",
            action="store_true",
        )
        parser.add_argument(
            "--reload-all",
            help="Recalculate all data in range",
            action="store_true",
        )
        parser.add_argument(
            "--dry-run",
            help="Only print what would be recalculated",
            action="store_true",
        )
        parser.add_argument(
            "--time-ranges",
            help="Override time ranges (hours, days, months, quarters, years); Separated by comma",
        )
        parser.add_argument(
            "--periods-count",
            help="Incerease recalculation of charts by more of default periods",
            default=1,
            type=int,
        )

    def get_all_multiseries_criteria(self, stats, options):
        all_multiseries_criteria = list(
            stats.criteriatostatsm2m_set.filter(use_as="multiple_series", recalculate=True)
        )
        all_multiseries_criteria.append("")
        return all_multiseries_criteria

    def handle(self, *args, **options):
        stats_query = DashboardStats.objects.filter(cache_values=True, show_to_users=False)
        if options.get("graph_key", None):
            stats_query = stats_query.filter(graph_key__in=options["graph_key"])
        if options.get("exclude", None):
            stats_query = stats_query.exclude(graph_key__in=options["exclude"].split(","))

        chart_string = "\n".join(
            f"\t{k.ljust(30)}\t{v}"
            for (k, v) in stats_query.values_list("graph_key", "graph_title")
        )
        print(f"recalculating charts: \n{chart_string}")
        for stats in stats_query:
            operation = stats.type_operation_field_name
            user = UserProfile.objects.get(email="petr.dlouhy@email.cz")
            configuration = {
                "select_box_chart_type": stats.default_chart_type,
                "reload": "True",
                "reload_all": str(options["reload_all"]),
            }
            for criteria in stats.criteriatostatsm2m_set.filter(
                use_as="chart_filter",
                criteria__dynamic_criteria_field_name__isnull=False,
            ):
                configuration[f"select_box_dynamic_{criteria.id}"] = criteria.default_option

            all_multiseries_criteria = self.get_all_multiseries_criteria(stats, options)

            print(f"recalculating {stats} controls")
            if not options["dry_run"]:
                stats.get_control_form_raw(user=user)

            for multiseries_criteria in all_multiseries_criteria:
                if multiseries_criteria:
                    configuration["select_box_multiple_series"] = multiseries_criteria.id

                if options.get("time_ranges", None):
                    time_scales = options["time_ranges"].split(",")
                else:
                    time_scales = stats.allowed_time_scales

                chart_tz = get_charts_timezone()
                for operation_field in stats.operation_field_name.split(","):
                    for selected_interval in time_scales:
                        print(
                            f"recalculating chart {stats} with {multiseries_criteria} on "
                            f"{operation_field} criteria in {selected_interval}"
                        )
                        time_since = datetime.now() - timedelta(
                            days=stats.default_time_period
                        ) * options.get("periods_count", 1)
                        time_since = truncate(time_since, Interval(selected_interval).val())
                        time_since = time_since.astimezone(chart_tz)

                        time_until = datetime.now()
                        time_until = truncate_ceiling(time_until, Interval(selected_interval).val())
                        time_until = time_until.astimezone(chart_tz)

                        configuration["select_box_interval"] = selected_interval
                        if not options["dry_run"]:
                            stats.get_multi_time_series_cached(
                                configuration=configuration,
                                time_since=time_since,
                                time_until=time_until,
                                interval=Interval(selected_interval),
                                operation_choice=operation,
                                operation_field_choice=operation_field,
                                user=user,
                            )
