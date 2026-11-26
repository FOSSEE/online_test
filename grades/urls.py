from django.urls import re_path
from grades import views

app_name = 'grades'

urlpatterns = [
    re_path(r'^$', views.grading_systems, name="grading_systems_home"),
    re_path(r'^grading_systems/$', views.grading_systems, name="grading_systems"),
    re_path(r'^add_grade/$', views.add_grading_system, name="add_grade"),
    re_path(r'^add_grade/(?P<system_id>\d+)/$', views.add_grading_system,
        name="edit_grade"),
]
