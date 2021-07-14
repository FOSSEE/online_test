# Python Imports
import os
from datetime import datetime
import pytz

# Django Imports
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)

# Local Imports
from grades.models import GradingSystem


def get_lesson_file_dir(instance, filename):
    if isinstance(instance, Lesson):
        upload_dir = f"lesson_{instance.id}"
    else:
        upload_dir = f"lesson_{instance.lesson.id}"
    return os.sep.join((upload_dir, filename))


def file_cleanup(sender, instance, *args, **kwargs):
    '''
        Deletes the file(s) associated with a model instance. The model
        is not saved after deletion of the file(s) since this is meant
        to be used with the pre_delete signal.
    '''
    for field_name, _ in instance.__dict__.items():
        field = getattr(instance, field_name)
        if issubclass(field.__class__, FieldFile) and field.name:
            field.delete(save=False)


class Course(models.Model):
    enrollment_methods = (
        ("default", "Enroll Request"),
        ("open", "Open Enrollment"),
    )
    name = models.CharField(max_length=255)
    enrollment = models.CharField(max_length=32, choices=enrollment_methods)
    active = models.BooleanField(default=True)
    code = models.CharField(max_length=128, null=True, blank=True)
    hidden = models.BooleanField(default=False)
    owner = models.ForeignKey(User, related_name='course_creator',
                                on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    is_trial = models.BooleanField(default=False)
    instructions = models.TextField(default=None, null=True, blank=True)
    view_grade = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    start_enroll_time = models.DateTimeField(
        "Start Date and Time for enrollment of course",
        default=timezone.now,
        null=True
    )
    end_enroll_time = models.DateTimeField(
        "End Date and Time for enrollment of course",
        default=datetime(
            2199, 1, 1,
            tzinfo=pytz.timezone(timezone.get_current_timezone_name())
        ),
        null=True
    )

    grading = models.OneToOneField(GradingSystem, null=True, blank=True,
                                related_name="course_grade",
                                on_delete=models.CASCADE)

    def get_modules(self):
        return self.modules.order_by("order")

    @property
    def creator_name(self):
        return self.owner.get_full_name()

    def is_valid_user(self, user_id):
        is_creator = self.owner_id == user_id
        is_teacher = CourseTeacher.objects.filter(
            course_id=self.id, teacher_id=user_id
        ).exists()
        return is_creator or is_teacher

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    enrollment_status = (
        (1, "Pending"),
        (2, "Rejected"),
        (3, "Enrolled"),
    )
    student = models.ForeignKey(
        User, related_name='student', on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course, related_name='course', on_delete=models.CASCADE
    )
    status = models.IntegerField(choices=enrollment_status)

    def __str__(self):
        return f"Enrollment status of {self.student} in {self.course}"


class CourseTeacher(models.Model):
    teacher = models.ForeignKey(
        User, related_name='teacher', on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course, related_name='allotted', on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.allotted_user.get_full_name()} teacher in {self.course}"


class Module(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(default=None, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course, related_name="modules", on_delete=models.CASCADE
    )
    order = models.IntegerField(default=0)
    html_data = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    @property
    def has_units(self):
        return self.units.exists()

    def __str__(self):
        return f"{self.name} created by {self.owner}"


class Unit(models.Model):
    module = models.ForeignKey(
        Module, related_name="units", on_delete=models.CASCADE
    )
    order = models.IntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    check_prerequisite = models.BooleanField(default=False)

    def __str__(self):
        return f"Unit for {self.module.name}"


class Lesson(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    html_data = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="lesson_creator"
    )
    active = models.BooleanField(default=True)
    video_file = models.FileField(
        upload_to=get_lesson_file_dir, max_length=255, default=None,
        null=True, blank=True
        )
    video_path = models.JSONField(
        default={}, null=True, blank=True,
        )
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    content = GenericRelation(Unit, related_query_name='lessons')

    def __str__(self):
        return f"{self.name} created by {self.owner}"

pre_delete.connect(file_cleanup, sender=Lesson)


class LessonFile(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="lesson",
                               on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_lesson_file_dir, default=None)

    def __str__(self):
        return f"{self.file.name} for {self.lesson.name}"

pre_delete.connect(file_cleanup, sender=LessonFile)
