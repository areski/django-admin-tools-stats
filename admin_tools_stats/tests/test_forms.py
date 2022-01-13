from django.test import TestCase
from model_bakery import baker

from admin_tools_stats.forms import ChartSettingsForm


class ChartSettingsFormTests(TestCase):
    def test_operations_list(self):
        stats = baker.make(
            "DashboardStats",
            allowed_type_operation_field_name=["Sum", "Count"],
            operation_field_name="auth,user",
        )
        ch = ChartSettingsForm(stats)
        self.assertEqual(
            ch.fields["select_box_operation_field"].choices,
            [("", "(divide all)"), ("auth", "auth"), ("user", "user")],
        )
