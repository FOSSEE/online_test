from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'online_test.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^exam/', include('yaksh.urls', namespace='yaksh', app_name='yaksh')),
    url(r'^exam/reset/', include('yaksh.urls_password_reset')),
    url(r'^', include('social.apps.django_app.urls', namespace='social')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
