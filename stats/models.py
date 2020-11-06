# Django Imports
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Local Imports
from yaksh.models import Course, Lesson


class TrackLesson(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    current_time = models.CharField(max_length=100, default="00:00:00")
    video_duration = models.CharField(max_length=100, default="00:00:00")
    last_access_time = models.DateTimeField(default=timezone.now)
    creation_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course', 'lesson')

    def __str__(self):
        return (f"Track {self.lesson} in {self.course} "
                f"for {self.user.get_full_name()}")
