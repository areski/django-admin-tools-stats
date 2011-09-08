from django.conf.urls.defaults import handler404, handler500, include,\
     patterns, url
from django.conf import settings
from django.conf.urls.i18n import *
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    # redirect
    #('^$', 'django.views.generic.simple.redirect_to',
    #{'url': '/dialer_campaign/'}),

    # Example:

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),

    (r'^admin_tools/', include('admin_tools.urls')),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT}),
)
