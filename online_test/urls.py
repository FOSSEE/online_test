from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'online_test.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
<<<<<<< HEAD
    url(r'^exam/', include('testapp.exam.urls')),
=======
    url(r'^exam/', include('testapp.yaksh_app.urls')),
    url(r'^taggit_autocomplete_modified/', include\
                                    ('taggit_autocomplete_modified.urls'))
>>>>>>> Change app name to yaksh
)
