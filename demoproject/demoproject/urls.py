from django.conf.urls import url, include

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from .views import home
admin.autodiscover()

urlpatterns = [
    url(r'^$', home, name='home'),

    # url(r'^demoproject/', include('demoproject.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^admin/', admin.site.urls),
]
