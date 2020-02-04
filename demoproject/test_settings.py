from .demoproject.settings import *  # noqa
from .demoproject.settings import INSTALLED_APPS

ROOT_URLCONF = 'demoproject.demoproject.urls'
ADMIN_TOOLS_MENU = 'demoproject.menu.CustomMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = 'demoproject.dashboard.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'demoproject.dashboard.CustomAppIndexDashboard'

INSTALLED_APPS.remove('demoproject')
INSTALLED_APPS.append('demoproject.demoproject')

FIXTURE_DIRS = (
       'demoproject/demoproject/fixtures/',
)
