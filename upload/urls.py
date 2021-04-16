from django.conf.urls import url
from upload import views

app_name = 'upload'

urlpatterns = [
    url(r'^download_course_md/(?P<course_id>\d+)/$',
        views.download_course_md, name="download_course_md"),
]