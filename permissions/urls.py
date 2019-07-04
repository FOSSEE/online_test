from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^create/team/$', views.create_team, name="create_team"),
    url(r'^delete/team/(?P<team_id>\d+)/', views.delete_team,
        name="delete_team"),
    url(r'^team/([0-9]+)/$', views.team_detail, name="team_detail"),
    url(r'^create/role/$', views.create_role, name="create_role"),
    url(r'^add/permission/$', views.add_permission, name="add_permission"),
    url(r'^delete/permission/(?P<permission_id>\d+)/(?P<team_id>\d+)/$',
        views.delete_permission,
        name="delete_permission"),
    url(r'^units/get/$', views.get_modules, name="get_modules"),
]
