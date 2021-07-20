from django.urls import path, include

from .views import PostComments, CoursePostList, LessonPostList

app_name = 'forum_api'


urlpatterns = [
    path('course_forum/<int:course_id>/', CoursePostList.as_view()),
    # path('course_forum/<int:course_id>/<int:post_id>/', CoursePostDetail.as_view()),
    path('course_forum/<int:course_id>/<int:post_id>/', PostComments.as_view()),
    # path('course_forum/<int:course_id>/<int:post_id>/<int:comment_id>/', PostCommentDetail.as_view()),
    path('lesson_forum/<int:course_id>/<int:lesson_id>/', LessonPostList.as_view())
]
