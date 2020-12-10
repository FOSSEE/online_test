# Python Imports
import pandas as pd

# Django Imports
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import F

# Local Imports
from yaksh.models import Course, Lesson


def str_to_datetime(s):
    return timezone.datetime.strptime(s, '%H:%M:%S')


def str_to_time(s):
    return timezone.datetime.strptime(s, '%H:%M:%S').time()


def time_to_seconds(time):
    return timezone.timedelta(hours=time.hour, minutes=time.minute,
                              seconds=time.second).total_seconds()


class TrackLessonManager(models.Manager):
    def get_percentage_data(self, tracked_lessons):
        percentage_data = {"1": 0, "2": 0, "3": 0, "4": 0}
        for tracked in tracked_lessons:
            percent = tracked.get_percentage_complete()
            if percent < 25:
                percentage_data["1"] = percentage_data["1"] + 1
            elif percent >= 25 and percent < 50:
                percentage_data["2"] = percentage_data["2"] + 1
            elif percent >= 50 and percent < 75:
                percentage_data["3"] = percentage_data["3"] + 1
            elif percent >= 75:
                percentage_data["4"] = percentage_data["4"] + 1
        return percentage_data


class TrackLesson(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    current_time = models.CharField(max_length=100, default="00:00:00")
    video_duration = models.CharField(max_length=100, default="00:00:00")
    creation_time = models.DateTimeField(auto_now_add=True)
    watched = models.BooleanField(default=False)

    objects = TrackLessonManager()

    class Meta:
        unique_together = ('user', 'course', 'lesson')

    def get_log_counter(self):
        return self.lessonlog_set.count()

    def get_current_time(self):
        if self.current_time == '00:00:00':
            return '00:00:00'
        return self.current_time

    def get_video_duration(self):
        if self.video_duration == '00:00:00':
            return '00:00:00'
        return self.video_duration

    def set_current_time(self, ct):
        t = timezone.datetime.strptime(ct, '%H:%M:%S').time()
        current = timezone.datetime.strptime(self.current_time,
                                             '%H:%M:%S').time()
        if t > current:
            self.current_time = ct

    def get_percentage_complete(self):
        ctime = self.current_time
        vduration = self.video_duration
        if ctime == '00:00:00' and vduration == '00:00:00':
            return 0
        duration = str_to_time(vduration)
        watch_time = str_to_time(ctime)
        duration_seconds = time_to_seconds(duration)
        watched_seconds = time_to_seconds(watch_time)
        percentage = round((watched_seconds / duration_seconds) * 100)
        return percentage

    def get_last_access_time(self):
        lesson_logs = self.lessonlog_set
        last_access_time = self.creation_time
        if lesson_logs.exists():
            last_access_time = lesson_logs.last().last_access_time
        return last_access_time

    def set_watched(self):
        ctime = self.current_time
        vduration = self.video_duration
        if ctime != '00:00:00' and vduration != '00:00:00':
            duration = str_to_time(vduration)
            watch_time = (str_to_datetime(ctime) + timezone.timedelta(
                seconds=120)).time()
            self.watched = watch_time >= duration

    def get_watched(self):
        if not self.watched:
            self.set_watched()
            self.save()
        return self.watched

    def time_spent(self):
        if self.video_duration != '00:00:00':
            hits = self.get_log_counter()
            duration = str_to_time(self.video_duration)
            hit_duration = int((time_to_seconds(duration))/4)
            total_duration = hits * hit_duration
            return str(timezone.timedelta(seconds=total_duration))
        return self.get_current_time()

    def get_no_of_vists(self):
        lesson_logs = self.lessonlog_set.values("last_access_time").annotate(
            visits=F('last_access_time')
        )
        df = pd.DataFrame(lesson_logs)
        visits = 1
        if not df.empty:
            visits = df.groupby(
                [df['visits'].dt.date]
            ).first().count()['visits']
        return visits

    def __str__(self):
        return (f"Track {self.lesson} in {self.course} "
                f"for {self.user.get_full_name()}")


class LessonLog(models.Model):
    track = models.ForeignKey(TrackLesson, on_delete=models.CASCADE)
    current_time = models.CharField(max_length=20, default="00:00:00")
    last_access_time = models.DateTimeField(default=timezone.now)
