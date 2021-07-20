from django.urls import path, include

from .views import CoursePostList, CoursePostDetail, CoursePostComments, \
                   CoursePostCommentDetail, LessonPostList, LessonPostDetail, \
                   LessonPostComments, LessonPostCommentDetail

app_name = 'forum_api'


urlpatterns = [
    path('course_forum/<int:course_id>/', CoursePostList.as_view()),
    path(
        'course_forum/<int:course_id>/<int:post_id>/',
         CoursePostDetail.as_view()
    ),
    path(
        'course_forum/<int:course_id>/<int:post_id>/comments/',
        CoursePostComments.as_view()
    ),
    path(
        'course_forum/<int:course_id>/<int:post_id>/comments/<int:comment_id>/',
        CoursePostCommentDetail.as_view()
    ),
    path(
        'lesson_forum/<int:course_id>/<int:lesson_id>/',
        LessonPostList.as_view()
    ),
    path(
        'lesson_forum/<int:course_id>/<int:lesson_id>/<int:post_id>/',
        LessonPostDetail.as_view()
    ),
    path(
        'lesson_forum/<int:course_id>/<int:lesson_id>/<int:post_id>/comments/',
        LessonPostComments.as_view()
    ),
    path(
        'lesson_forum/<int:course_id>/<int:lesson_id>/<int:post_id>/comments/<int:comment_id>/',
        LessonPostCommentDetail.as_view()
    ),
]
