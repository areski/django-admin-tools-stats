from django.test.utils import override_settings
from django.urls import reverse
from model_mommy import mommy

from .utils import BaseSuperuserAuthenticatedClient


class AdminIndexTests(BaseSuperuserAuthenticatedClient):
    def setUp(self):
        self.stats = mommy.make(
            'DashboardStats',
            graph_title="User chart",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            operation_field_name='is_active,is_staff',
        )
        super().setUp()

    @override_settings(
        INSTALLED_APPS=[
            'django_nvd3',
            'admin_tools_stats',
            'admin_tools.menu',
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'djangobower',
            'demoproject',
        ]
    )
    def test_admin_index(self):
        """Test vanila admin index page, that should contain chart"""
        url = reverse('admin:index')
        response = self.client.get(url)
        self.assertContains(response, "<h3>User chart</h3>", html=True)
        self.assertContains(
            response,
            '<select name="select_box_operation_field" class="chart-input" required>'
            '<option value="">(divide all)</option>'
            '<option value="is_active" selected>is_active</option>'
            '<option value="is_staff">is_staff</option>'
            '</select>',
            html=True,
        )
