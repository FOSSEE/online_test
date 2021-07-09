from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from yaksh.courses import views

urlpatterns = [
    path('courses', views.CourseListDetail.as_view()),
    path('course', views.CourseDetail.as_view()),
    path('course/<int:pk>', views.CourseDetail.as_view()),
    path('modules/<int:course_id>', views.ModuleListDetail.as_view()),
    path('module', views.ModuleDetail.as_view()),
    path('module/<int:pk>', views.ModuleDetail.as_view()),
    path('lesson/<int:module_id>', views.LessonDetail.as_view()),
    path('lesson/<int:pk>/', views.LessonDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)