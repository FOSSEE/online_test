from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from settings import URL_ROOT

if URL_ROOT.startswith('/'):
    URL_BASE = r'^%s/exam/'%URL_ROOT[1:]
    ADMIN_BASE = r'^%s/admin/'%URL_ROOT[1:]
else:
    URL_BASE = r'^exam/'
    ADMIN_BASE = r'^admin/'

urlpatterns = patterns('',
    url(URL_BASE, include('exam.urls')),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(ADMIN_BASE, include(admin.site.urls)),
)
