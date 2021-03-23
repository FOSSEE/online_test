from django.urls import path
from stats import views


app_name = "stats"

urlpatterns = [
    path('submit/video/watch/<int:tracker_id>',
         views.add_tracker, name='add_tracker'),
    path('view/watch/stats/<int:course_id>/<int:lesson_id>',
         views.view_lesson_watch_stats, name='view_lesson_watch_stats'),
]
