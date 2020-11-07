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
    creation_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course', 'lesson')

    def get_last_access_time_and_vists(self):
        lesson_logs = self.lessonlog_set
        last_access_time = None
        if lesson_logs.exists():
            last_access_time = lesson_logs.last().last_access_time
        return last_access_time, lesson_logs.count()

    def __str__(self):
        return (f"Track {self.lesson} in {self.course} "
                f"for {self.user.get_full_name()}")


class LessonLog(models.Model):
    track = models.ForeignKey(TrackLesson, on_delete=models.CASCADE)
    last_access_time = models.DateTimeField(default=timezone.now)
