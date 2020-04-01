from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

app_name = 'api'

urlpatterns = [
    url(r'questions/$', views.QuestionList.as_view(), name='questions'),
    url(r'questions/(?P<pk>[0-9]+)/$', views.QuestionDetail.as_view(),
        name='question'),
    url(r'get_courses/$', views.CourseList.as_view(), name='get_courses'),
    url(r'start_quiz/(?P<course_id>[0-9]+)/(?P<quiz_id>[0-9]+)/$', views.StartQuiz.as_view(),
        name='start_quiz'),
    url(r'quizzes/$', views.QuizList.as_view(), name='quizzes'),
    url(r'quizzes/(?P<pk>[0-9]+)/$', views.QuizDetail.as_view(), name='quiz'),
    url(r'questionpapers/$', views.QuestionPaperList.as_view(),
        name='questionpapers'),
    url(r'questionpapers/(?P<pk>[0-9]+)/$',
        views.QuestionPaperDetail.as_view(), name='questionpaper'),
    url(r'answerpapers/$', views.AnswerPaperList.as_view(),
        name='answerpapers'),
    url(r'validate/(?P<answerpaper_id>[0-9]+)/(?P<question_id>[0-9]+)/$',
        views.AnswerValidator.as_view(), name='validators'),
    url(r'validate/(?P<uid>[0-9]+)/$',
        views.AnswerValidator.as_view(), name='validator'),
    url(r'course/(?P<pk>[0-9]+)/$',
        views.GetCourse.as_view(), name='get_course'),
    url(r'quit/(?P<answerpaper_id>\d+)/$', views.QuitQuiz.as_view(),
        name="quit_quiz"),
    url(r'login/$', views.login, name='login')
]

urlpatterns = format_suffix_patterns(urlpatterns)
