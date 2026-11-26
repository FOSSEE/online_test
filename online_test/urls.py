from django.urls import include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from online_test import views
admin.autodiscover()

urlpatterns = [
    # Examples:
    # re_path(r'^$', 'online_test.views.home', name='home'),
    # re_path(r'^blog/', include('blog.urls')),

    re_path(r'^admin/', admin.site.urls),
    re_path(r'^$', views.index, name='index'),
    re_path(r'^exam/', include(('yaksh.urls', 'yaksh'))),
    re_path(r'', include('yaksh.urls_password_reset')),
    re_path(r'^', include('social_django.urls', namespace='social')),
    re_path(r'^grades/', include(('grades.urls', 'grades'))),
    re_path(r'^api/', include('api.urls', namespace='api')),
    re_path(r'^stats/', include('stats.urls', namespace='stats')),
    re_path(r'^flatfiles/', include(('upload.urls', 'upload'))),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
