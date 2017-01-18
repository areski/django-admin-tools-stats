from .demoproject.settings import *

ROOT_URLCONF = 'demoproject.demoproject.urls'
ADMIN_TOOLS_MENU = 'demoproject.menu.CustomMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = 'demoproject.dashboard.CustomIndexDashboard'
ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'demoproject.dashboard.CustomAppIndexDashboard'

FIXTURE_DIRS = (
       'demoproject/demoproject/fixtures/',
)
