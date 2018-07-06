from django.conf.urls import url
from analysis import views

urlpatterns = [
    url(r'^final_summary/$', views.final_summary, name='final_summary'),
    url(r'^final_summary_data/$', views.final_summary_data,
        name='final_summary_data'),
    url(r'^view_quiz_stats/(?P<course_id>\d+)/(?P<question_paper_id>\d+)/$',
        views.view_quiz_stats, name='view_quiz_stats'),
]
