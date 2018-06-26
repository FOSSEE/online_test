from django.conf.urls import url
from . import views

urlpatterns = [
    
    url(r'^$', views.post_list, name='post_list'),
    url(r'new/(?P<pk>\d+)/$', views.post_detail, name='post_detail'),
    url(r'new/$', views.post_new, name='post_new'),

]