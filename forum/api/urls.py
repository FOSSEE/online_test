from django.urls import path
from .views import course_post_list, course_post_detail, lesson_post_list

app_name = 'forum_api'

urlpatterns = [
    path('course_forum/<int:course_id>/', course_post_list),
    path('course_forum/<int:course_id>/<int:post_id>/', course_post_detail),
    path('lesson_forum/<int:course_id>/', lesson_post_list),
]
