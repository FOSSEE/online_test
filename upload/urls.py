from django.urls import re_path
from upload import views

app_name = 'upload'

urlpatterns = [
    re_path(r'^download_course_md/(?P<course_id>\d+)/$',
        views.download_course_md, name="download_course_md"),
]
