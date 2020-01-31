from django.contrib import admin
from django.urls import include, path

from .views import home
admin.autodiscover()

urlpatterns = [
    path('', home, name='home'),

    # url(r'^demoproject/', include('demoproject.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    path('admin_tools_stats/', include('admin_tools_stats.urls')),
    path('admin_tools/', include('admin_tools.urls')),
    path('admin/', admin.site.urls),
]
