from django.conf.urls import patterns, url
from certificates import views

urlpatterns = [
    url(r'^preview/(?P<course_id>\d+)/$', views.preview_certificate, name='preview_certificate'),
    url(r'^add/(?P<course_id>\d+)/$', views.add_certificate, name='add_certificate'),
    url(r'^download/(?P<course_id>\d+)/$', views.download_certificate, name='download_certificate'),
]