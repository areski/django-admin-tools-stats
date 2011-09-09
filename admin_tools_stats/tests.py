from django.contrib.auth.models import User
from django.test import TestCase, Client
from admin_tools_stats.test_utils import build_test_suite_from
import base64


class AdminToolsStatsAdminInterfaceTestCase(TestCase):
    """Test cases for django-admin-tools-stats Admin Interface."""

    def setUp(self):
        """To create an admin username"""
        self.client = Client()
        self.user = \
        User.objects.create_user('admin', 'admin@world.com', 'admin')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.is_active = True
        self.user.save()
        auth = '%s:%s' % ('admin', 'admin')
        auth = 'Basic %s' % base64.encodestring(auth)
        auth = auth.strip()
        self.extra = {
            'HTTP_AUTHORIZATION': auth,
        }

    def test_admin_index(self):
        """Test function to check admin index page."""
        response = self.client.get('/admin/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.login(username=self.user.username,
                                     password='admin')
        self.assertEqual(response, True)

    def test_admin_tools_stats(self):
        """Test function to check django-admin-tools-stats admin pages"""
        response = self.client.get('/admin/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/auth/')
        self.failUnlessEqual(response.status_code, 200)
        
        response = self.client.get('/admin/admin_tools_stats/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/admin/admin_tools_stats/dashboardstats/')
        self.failUnlessEqual(response.status_code, 200)
        response = \
        self.client.get('/admin/admin_tools_stats/dashboardstatscriteria/')
        self.failUnlessEqual(response.status_code, 200)



test_cases = [
    AdminToolsStatsAdminInterfaceTestCase,
]


def suite():
    return build_test_suite_from(test_cases)
