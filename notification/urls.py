from django.conf.urls import url

from . import views

app_name = 'notification'

urlpatterns = [
    url(r'(?P<course_id>\d+)/$', views.toggle_subscription_status, name="toggle_subscription_status"),

]
