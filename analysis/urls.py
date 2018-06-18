from django.conf.urls import url
from analysis import views

urlpatterns = [
	url(r'^final_summary/$', views.final_summary),
	url(r'^final_summary_data/$', views.final_summary_data),
	]