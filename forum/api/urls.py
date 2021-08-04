from django.urls import path, include

from .views import CoursePostList, CoursePostDetail, CoursePostComments, \
                   CoursePostCommentDetail, LessonPostDetail, \
                   LessonPostComments, LessonPostCommentDetail

app_name = 'forum_api'


urlpatterns = [
    path('course_forum/<int:course_id>/', CoursePostList.as_view(), name='course_post_list'),
    path(
        'course_forum/<int:course_id>/<int:post_id>/',
         CoursePostDetail.as_view(),
         name='course_post_detail'
    ),
    path(
        'course_forum/<int:course_id>/<int:post_id>/comments/',
        CoursePostComments.as_view(),
        name='course_post_comments'
    ),
    path(
        'course_forum/<int:course_id>/<int:post_id>/comments/<int:comment_id>/',
        CoursePostCommentDetail.as_view(),
        name='course_post_comment_detail'
    ),
    path(
        'lesson_forum/<int:course_id>/<int:lesson_id>/',
        LessonPostDetail.as_view(),
        name='lesson_post_detail'
    ),
    path(
        'lesson_forum/<int:course_id>/<int:lesson_id>/<int:post_id>/comments/',
        LessonPostComments.as_view(),
        name='lesson_post_comments'
    ),
    path(
        'lesson_forum/<int:course_id>/<int:lesson_id>/<int:post_id>/comments/<int:comment_id>/',
        LessonPostCommentDetail.as_view(),
        name='lesson_post_comment_detail'
    ),
]
