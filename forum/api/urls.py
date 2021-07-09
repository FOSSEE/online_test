from django.urls import path
from .views import post_list

app_name = 'forum_api'

urlpatterns = [
    path('course_forum/<int:course_id>/', post_list),
]
