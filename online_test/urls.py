from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from online_test import views
admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'online_test.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index, name='index'),
    url(r'^exam/', include(('yaksh.urls', 'yaksh'))),
    url(r'^exam/reset/', include('django.contrib.auth.urls')),
    url(r'^', include('social_django.urls', namespace='social')),
    url(r'^grades/', include(('grades.urls', 'grades'))),
    url(r'^api/', include('api.urls', namespace='api')),
    url(r'^stats/', include('stats.urls', namespace='stats')),
    url(r'^flatfiles/', include(('upload.urls', 'upload'))),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
