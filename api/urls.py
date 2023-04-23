from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

from rest_framework.routers import SimpleRouter
from django.urls import path, include

app_name = 'api'

router = SimpleRouter()
router.register(r'questions', views.QuestionViewSet, basename='question')
router.register(r'quizzes', views.QuizViewSet, basename='quiz')


urlpatterns = [
    path('', include(router.urls)),
    url(r'get_courses/$', views.CourseList.as_view(), name='get_courses'),
    url(r'start_quiz/(?P<course_id>[0-9]+)/(?P<quiz_id>[0-9]+)/$', views.StartQuiz.as_view(),
        name='start_quiz'),
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
    url(r'login/$', views.login, name='login'),
    url(r'questionpapers/$', views.QuestionPaperList.as_view(),
        name='questionpapers'),
    url(r'questionpapers/(?P<pk>[0-9]+)/$',
        views.QuestionPaperDetail.as_view(), name='questionpaper'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
