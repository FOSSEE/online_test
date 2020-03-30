from django.conf.urls import url
from grades import views

app_name = 'grades'

urlpatterns = [
    url(r'^$', views.grading_systems, name="grading_systems_home"),
    url(r'^grading_systems/$', views.grading_systems, name="grading_systems"),
    url(r'^add_grade/$', views.add_grading_system, name="add_grade"),
    url(r'^add_grade/(?P<system_id>\d+)/$', views.add_grading_system,
        name="edit_grade"),
]
