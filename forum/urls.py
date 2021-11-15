from django.conf.urls import url
from django.urls import path
from forum import views

app_name = 'forum'

urlpatterns = [
    url(
        r'^course_forum/(?P<course_id>\d+)/$',
        views.course_forum,
        name='course_forum'
    ),
    url(
        r'^lessons_forum/(?P<course_id>\d+)/$',
        views.lessons_forum,
        name='lessons_forum'
    ),
    url(
        r'^(?P<course_id>\d+)/post/(?P<uuid>[0-9a-f-]+)/$',
        views.post_comments,
        name='post_comments'
    ),
    url(
        r'^(?P<course_id>\d+)/post/(?P<uuid>[0-9a-f-]+)/delete/',
        views.hide_post,
        name='hide_post'
    ),
    url(
        r'^(?P<course_id>\d+)/comment/(?P<uuid>[0-9a-f-]+)/delete/',
        views.hide_comment,
        name='hide_comment'
    ),
    url(
         r'^courseforum/(?P<course_id>\d+)/$',
        views.courseforum,
        name='courseforum'
    ),
    # url(
    #     r'^' lesson_forum
    # )
    url(
        r'^courseforum/(?P<course_id>\d+)/post/(?P<id>\d+)/$',
        views.postcomments,
        name='postcomments'
    ),
]