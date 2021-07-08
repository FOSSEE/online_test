# Python Imports
from __future__ import unicode_literals, division
from datetime import datetime, timedelta
import uuid
import json
import random
import ruamel.yaml
from ruamel.yaml.scalarstring import PreservedScalarString
from ruamel.yaml.comments import CommentedMap
from random import sample
from collections import Counter, defaultdict
import glob
import sys
import traceback
try:
    from StringIO import StringIO as string_io
except ImportError:
    from io import BytesIO as string_io
import pytz
import os
import stat
from os.path import join, exists
import shutil
import zipfile
import tempfile
from textwrap import dedent
from ast import literal_eval
import pandas as pd
import qrcode
import hashlib

# Django Imports
from django.db import models, IntegrityError
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from taggit.managers import TaggableManager
from django.utils import timezone
from django.core.files import File
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from django.contrib.contenttypes.models import ContentType
from django.template import Context, Template
from django.conf import settings
from django.forms.models import model_to_dict
from django.db.models import Count
from django.db.models.signals import pre_delete
from django.db.models.fields.files import FieldFile
from django.core.files.base import ContentFile
# Local Imports
from yaksh.code_server import (
    submit, get_result as get_result_from_code_server
)
from yaksh.settings import SERVER_POOL_PORT, SERVER_HOST_NAME
from .file_utils import extract_files, delete_files
from grades.models import GradingSystem


languages = (
        ("python", "Python"),
        ("bash", "Bash"),
        ("c", "C Language"),
        ("cpp", "C++ Language"),
        ("java", "Java Language"),
        ("scilab", "Scilab"),
        ("r", "R"),
        ("other", "Other")
    )

question_types = (
        ("mcq", "Single Correct Choice"),
        ("mcc", "Multiple Correct Choices"),
        ("code", "Code"),
        ("upload", "Assignment Upload"),
        ("integer", "Answer in Integer"),
        ("string", "Answer in String"),
        ("float", "Answer in Float"),
        ("arrange", "Arrange in Correct Order"),

    )

enrollment_methods = (
    ("default", "Enroll Request"),
    ("open", "Open Enrollment"),
    )

test_case_types = (
        ("standardtestcase", "Standard Testcase"),
        ("stdiobasedtestcase", "StdIO Based Testcase"),
        ("mcqtestcase", "MCQ Testcase"),
        ("hooktestcase", "Hook Testcase"),
        ("integertestcase", "Integer Testcase"),
        ("stringtestcase", "String Testcase"),
        ("floattestcase", "Float Testcase"),
        ("arrangetestcase", "Arrange Testcase"),
    )

string_check_type = (
    ("lower", "Case Insensitive"),
    ("exact", "Case Sensitive"),
    )

legend_display_types = {
        "mcq": {"label": "Objective Type"},
        "mcc": {"label": "Objective Type"},
        "code": {"label": "Programming"},
        "upload": {"label": "Upload"},
        "integer": {"label": "Objective Type"},
        "string": {"label": "Objective Type"},
        "float": {"label": "Objective Type"},
        "arrange": {"label": "Objective Type"},
    }

attempts = [(i, i) for i in range(1, 6)]
attempts.append((-1, 'Infinite'))

test_status = (
                ('inprogress', 'Inprogress'),
                ('completed', 'Completed'),
              )

FIXTURES_DIR_PATH = os.path.join(settings.BASE_DIR, 'yaksh', 'fixtures')

MOD_GROUP_NAME = 'moderator'


def get_assignment_dir(instance, filename):
    course_id = instance.answer_paper.course_id
    quiz_id = instance.answer_paper.question_paper.quiz_id
    folder = f'Course_{course_id}'
    sub_folder = f'Quiz_{quiz_id}'
    user = instance.answer_paper.user.username
    return os.sep.join((folder, sub_folder, user,
                        str(instance.assignmentQuestion_id),
                        filename
                        ))


def get_model_class(model):
    ctype = ContentType.objects.get(app_label="yaksh", model=model)
    model_class = ctype.model_class()

    return model_class


def get_upload_dir(instance, filename):
    return os.sep.join((
        'question_%s' % (instance.question.id), filename
    ))


def dict_to_yaml(dictionary):
    for k, v in dictionary.items():
        if isinstance(v, list):
            for nested_v in v:
                if isinstance(nested_v, dict):
                    dict_to_yaml(nested_v)
        elif v and isinstance(v, str):
            dictionary[k] = PreservedScalarString(v)
    return ruamel.yaml.round_trip_dump(dictionary, explicit_start=True,
                                       default_flow_style=False,
                                       allow_unicode=True,
                                       )


def get_file_dir(instance, filename):
    if isinstance(instance, LessonFile):
        upload_dir = f"Lesson_{instance.lesson.id}"
    else:
        upload_dir = f"Lesson_{instance.id}"
    return os.sep.join((upload_dir, filename))


def create_group(group_name, app_label):
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        group = Group(name=group_name)
        group.save()
        # Get the models for the given app
        content_types = ContentType.objects.filter(app_label=app_label)
        # Get list of permissions for the models
        permission_list = Permission.objects.filter(
            content_type__in=content_types)
        group.permissions.add(*permission_list)
        group.save()
    return group


def write_static_files_to_zip(zipfile, course_name, current_dir, static_files):
    """ Write static files to zip

        Parameters
        ----------

        zipfile : Zipfile object
            zip file in which the static files need to be added

        course_name : str
            Create a folder with course name

        current_dir: str
            Path from which the static files will be taken

        static_files: dict
            Dictionary containing static folders as keys and static files as
            values
    """
    for folder in static_files.keys():
        folder_path = os.sep.join((current_dir, "static", "yaksh", folder))
        for file in static_files[folder]:
            file_path = os.sep.join((folder_path, file))
            with open(file_path, "rb") as f:
                zipfile.writestr(
                    os.sep.join((course_name, "static", folder, file)),
                    f.read()
                    )


def write_templates_to_zip(zipfile, template_path, data, filename, filepath):
    """ Write template files to zip

        Parameters
        ----------

        zipfile : Zipfile object
            zip file in which the template files need to be added

        template_path : str
            Path from which the template file will be loaded

        data: dict
            Dictionary containing context data required for template

        filename: str
            Filename with which the template file should be named

        filepath: str
            File path in zip where the template will be added
    """
    rendered_template = render_template(template_path, data)
    zipfile.writestr(os.sep.join((filepath, "{0}.html".format(filename))),
                     str(rendered_template))


def render_template(template_path, data=None):
    with open(template_path) as f:
        template_data = f.read()
        template = Template(template_data)
        context = Context(data)
        render = template.render(context)
    return render


def validate_image(image):
    file_size = image.file.size
    limit_mb = 30
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError("Max size of file is {0} MB".format(limit_mb))


def get_image_dir(instance, filename):
    return os.sep.join((
        'post_%s' % (instance.uid), filename
    ))


def is_valid_time_format(time):
    try:
        hh, mm, ss = time.split(":")
        status = True
    except ValueError:
        status = False
    return status


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

###############################################################################
class CourseManager(models.Manager):

    def create_trial_course(self, user):
        """Creates a trial course for testing questions"""
        trial_course = self.create(name="trial_course", enrollment="open",
                                   creator=user, is_trial=True)
        trial_course.enroll(False, user)
        return trial_course

    def get_hidden_courses(self, code):
        return self.filter(code=code, hidden=True)


#############################################################################
class Lesson(models.Model):
    # Lesson name
    name = models.CharField(max_length=255)

    # Markdown text of lesson content
    description = models.TextField()

    # Markdown text should be in html format
    html_data = models.TextField(null=True, blank=True)

    # Creator of the lesson
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    # Activate/Deactivate Lesson
    active = models.BooleanField(default=True)

    # A video file
    video_file = models.FileField(
        upload_to=get_file_dir, max_length=255, default=None,
        null=True, blank=True,
        help_text="Please upload video files in mp4, ogv, webm format"
        )

    video_path = models.CharField(
        max_length=255, default=None, null=True, blank=True,
        help_text="Youtube id, vimeo id, others"
        )

    def __str__(self):
        return "{0}".format(self.name)

    def get_files(self):
        return LessonFile.objects.filter(lesson_id=self.id)

    def _create_lesson_copy(self, user):
        lesson_files = self.get_files()
        new_lesson = self
        new_lesson.id = None
        new_lesson.creator = user
        new_lesson.save()
        for _file in lesson_files:
            try:
                file_name = os.path.basename(_file.file.name)
                lesson_file = ContentFile(_file.file.read())
                new_lesson_file = LessonFile()
                new_lesson_file.lesson_id=self.id
                new_lesson_file.file.save(file_name, lesson_file, save=True)
                new_lesson_file.save()
            except FileNotFoundError:
                pass
        return new_lesson

    def remove_file(self):
        self.video_file.delete()

    def _add_lesson_to_zip(self, next_unit, module, course, zip_file, path):
        lesson_name = self.name.replace(" ", "_")
        course_name = course.name.replace(" ", "_")
        module_name = module.name.replace(" ", "_")
        sub_folder_name = os.sep.join((
            course_name, module_name, lesson_name
            ))
        lesson_files = self.get_files()
        if self.video_file:
            video_file = os.sep.join((sub_folder_name, os.path.basename(
                        self.video_file.name)))
            zip_file.writestr(video_file, self.video_file.read())
        for lesson_file in lesson_files:
            if os.path.exists(lesson_file.file.path):
                filename = os.sep.join((sub_folder_name, os.path.basename(
                    lesson_file.file.name)))
                zip_file.writestr(filename, lesson_file.file.read())
        unit_file_path = os.sep.join((
            path, "templates", "yaksh", "download_course_templates",
            "unit.html"
            ))
        lesson_data = {"course": course, "module": module,
                       "lesson": self, "next_unit": next_unit,
                       "lesson_files": lesson_files}
        write_templates_to_zip(zip_file, unit_file_path, lesson_data,
                               lesson_name, sub_folder_name)

pre_delete.connect(file_cleanup, sender=Lesson)

#############################################################################
class LessonFile(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="lesson",
                               on_delete=models.CASCADE)
    file = models.FileField(upload_to=get_file_dir, default=None)

pre_delete.connect(file_cleanup, sender=LessonFile)

###############################################################################
class QuizManager(models.Manager):
    def get_active_quizzes(self):
        return self.filter(active=True, is_trial=False)

    def create_trial_quiz(self, user):
        """Creates a trial quiz for testing questions"""
        trial_quiz = self.create(
            duration=1000, description="trial_questions",
            is_trial=True, time_between_attempts=0, creator=user
            )
        return trial_quiz

    def create_trial_from_quiz(self, original_quiz_id, user, godmode,
                               course_id):
        """Creates a trial quiz from existing quiz"""
        trial_course_name = "Trial_course_for_course_{0}_{1}".format(
            course_id, "godmode" if godmode else "usermode")
        trial_quiz_name = "Trial_orig_id_{0}_{1}".format(
            original_quiz_id,
            "godmode" if godmode else "usermode"
        )
        # Get or create Trial Course for usermode/godmode
        trial_course = Course.objects.filter(name=trial_course_name)
        if trial_course.exists():
            trial_course = trial_course.get(name=trial_course_name)
        else:
            trial_course = Course.objects.create(
                name=trial_course_name, creator=user, enrollment="open",
                is_trial=True)

        # Get or create Trial Quiz for usermode/godmode
        if self.filter(description=trial_quiz_name).exists():
            trial_quiz = self.get(description=trial_quiz_name)

        else:
            trial_quiz = self.get(id=original_quiz_id)
            trial_quiz.user = user
            trial_quiz.pk = None
            trial_quiz.description = trial_quiz_name
            trial_quiz.is_trial = True
            trial_quiz.prerequisite = None
            if godmode:
                trial_quiz.time_between_attempts = 0
                trial_quiz.duration = 1000
                trial_quiz.attempts_allowed = -1
                trial_quiz.active = True
                trial_quiz.start_date_time = timezone.now()
                trial_quiz.end_date_time = datetime(
                    2199, 1, 1, 0, 0, 0, 0, tzinfo=pytz.utc
                )
            trial_quiz.save()

        # Get or create Trial Ordered Lesson for usermode/godmode
        learning_modules = trial_course.get_learning_modules()
        if learning_modules:
            quiz = learning_modules[0].learning_unit.filter(quiz=trial_quiz)
            if not quiz.exists():
                trial_learning_unit = LearningUnit.objects.create(
                    order=1, quiz=trial_quiz, type="quiz",
                    check_prerequisite=False)
                learning_modules[0].learning_unit.add(trial_learning_unit.id)
            trial_learning_module = learning_modules[0]
        else:
            trial_learning_module = LearningModule.objects.create(
                name="Trial for {}".format(trial_course), order=1,
                check_prerequisite=False, creator=user, is_trial=True)
            trial_learning_unit = LearningUnit.objects.create(
                order=1, quiz=trial_quiz, type="quiz",
                check_prerequisite=False)
            trial_learning_module.learning_unit.add(trial_learning_unit.id)
            trial_course.learning_module.add(trial_learning_module.id)

        # Add user to trial_course
        trial_course.enroll(False, user)
        return trial_quiz, trial_course, trial_learning_module


###############################################################################
class Quiz(models.Model):
    """A quiz that students will participate in. One can think of this
    as the "examination" event.
    """

    # The start date of the quiz.
    start_date_time = models.DateTimeField(
        "Start Date and Time of the quiz",
        default=timezone.now,
        null=True
    )

    # The end date and time of the quiz
    end_date_time = models.DateTimeField(
        "End Date and Time of the quiz",
        default=datetime(
            2199, 1, 1,
            tzinfo=pytz.timezone(timezone.get_current_timezone_name())
        ),
        null=True
    )

    # This is always in minutes.
    duration = models.IntegerField("Duration of quiz in minutes", default=20)

    # Is the quiz active. The admin should deactivate the quiz once it is
    # complete.
    active = models.BooleanField(default=True)

    # Description of quiz.
    description = models.CharField(max_length=256)

    # Mininum passing percentage condition.
    pass_criteria = models.FloatField("Passing percentage", default=40)

    # Number of attempts for the quiz
    attempts_allowed = models.IntegerField(default=1, choices=attempts)

    time_between_attempts = models.FloatField(
        "Time Between Quiz Attempts in hours", default=0.0
    )

    is_trial = models.BooleanField(default=False)

    instructions = models.TextField('Instructions for Students',
                                    default=None, blank=True, null=True)

    view_answerpaper = models.BooleanField('Allow student to view their answer\
                                            paper', default=False)

    allow_skip = models.BooleanField("Allow students to skip questions",
                                     default=True)

    weightage = models.FloatField(help_text='Will be considered as percentage',
                                  default=100)

    is_exercise = models.BooleanField(default=False)

    creator = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    objects = QuizManager()

    class Meta:
        verbose_name_plural = "Quizzes"

    def is_expired(self):
        return not self.start_date_time <= timezone.now() < self.end_date_time

    def create_demo_quiz(self, user):
        demo_quiz = Quiz.objects.create(
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(176590),
            duration=30, active=True,
            attempts_allowed=-1, time_between_attempts=0,
            description='Yaksh Demo quiz', pass_criteria=0,
            creator=user, instructions="<b>This is a demo quiz.</b>"
        )
        return demo_quiz

    def get_total_students(self, course):
        try:
            qp = self.questionpaper_set.get().id
        except QuestionPaper.DoesNotExist:
            qp = None
        return AnswerPaper.objects.filter(
                question_paper=qp,
                course=course
            ).values_list("user", flat=True).distinct().count()

    def get_passed_students(self, course):
        try:
            qp = self.questionpaper_set.get().id
        except QuestionPaper.DoesNotExist:
            qp = None
        return AnswerPaper.objects.filter(
                question_paper=qp,
                course=course, passed=True
            ).values_list("user", flat=True).distinct().count()

    def get_failed_students(self, course):
        try:
            qp = self.questionpaper_set.get().id
        except QuestionPaper.DoesNotExist:
            qp = None
        return AnswerPaper.objects.filter(
                question_paper=qp,
                course=course, passed=False
            ).values_list("user", flat=True).distinct().count()

    def get_answerpaper_status(self, user, course):
        try:
            qp = self.questionpaper_set.get().id
        except QuestionPaper.DoesNotExist:
            qp = None
        ans_ppr = AnswerPaper.objects.filter(
            user_id=user.id, course_id=course.id, question_paper_id=qp
        ).order_by("-attempt_number")
        if ans_ppr.exists():
            status = ans_ppr.first().status
        else:
            status = "not attempted"
        return status

    def get_answerpaper_passing_status(self, user, course):
        try:
            qp = self.questionpaper_set.get().id
        except QuestionPaper.DoesNotExist:
            qp = None
        ans_ppr = AnswerPaper.objects.filter(
            user_id=user.id, course_id=course.id, question_paper_id=qp
        ).order_by("-attempt_number")
        if ans_ppr.exists():
            return any([paper.passed for paper in ans_ppr])
        return False

    def _create_quiz_copy(self, user):
        question_papers = self.questionpaper_set.all()
        new_quiz = self
        new_quiz.id = None
        new_quiz.creator = user
        new_quiz.save()
        for qp in question_papers:
            qp._create_duplicate_questionpaper(new_quiz)
        return new_quiz

    def __str__(self):
        desc = self.description or 'Quiz'
        return '%s: on %s for %d minutes' % (desc, self.start_date_time,
                                             self.duration)

    def _add_quiz_to_zip(self, next_unit, module, course, zip_file, path):
        quiz_name = self.description.replace(" ", "_")
        course_name = course.name.replace(" ", "_")
        module_name = module.name.replace(" ", "_")
        sub_folder_name = os.sep.join((
            course_name, module_name, quiz_name
            ))
        unit_file_path = os.sep.join((
            path, "templates", "yaksh", "download_course_templates",
            "quiz.html"
            ))
        quiz_data = {"course": course, "module": module,
                     "quiz": self, "next_unit": next_unit}

        write_templates_to_zip(zip_file, unit_file_path, quiz_data,
                               quiz_name, sub_folder_name)


##########################################################################
class LearningUnit(models.Model):
    """ Maintain order of lesson and quiz added in the course """
    order = models.IntegerField()
    type = models.CharField(max_length=16)
    lesson = models.ForeignKey(Lesson, null=True, blank=True,
                               on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, null=True, blank=True,
                             on_delete=models.CASCADE)
    check_prerequisite = models.BooleanField(default=False)

    def get_lesson_or_quiz(self):
        unit = None
        if self.type == 'lesson':
            unit = self.lesson
        else:
            unit = self.quiz
        return unit

    def toggle_check_prerequisite(self):
        if self.check_prerequisite:
            self.check_prerequisite = False
        else:
            self.check_prerequisite = True

    def get_completion_status(self, user, course):
        course_status = CourseStatus.objects.filter(
            user_id=user.id, course_id=course.id
        )
        state = "not attempted"
        if course_status.exists():
            if course_status.first().completed_units.filter(id=self.id):
                state = "completed"
            elif self.type == "quiz":
                state = self.quiz.get_answerpaper_status(user, course)
            elif course_status.first().current_unit == self:
                state = "inprogress"
        return state

    def has_prerequisite(self):
        return self.check_prerequisite

    def is_prerequisite_complete(self, user, learning_module, course):
        ordered_units = learning_module.learning_unit.order_by("order")
        ordered_units_ids = list(ordered_units.values_list("id", flat=True))
        current_unit_index = ordered_units_ids.index(self.id)
        if current_unit_index == 0:
            success = True
        else:
            prev_unit = ordered_units.get(
                id=ordered_units_ids[current_unit_index-1])
            status = prev_unit.get_completion_status(user, course)
            if status == "completed":
                success = True
            else:
                success = False
        return success

    def _create_unit_copy(self, user):
        if self.type == "quiz":
            new_quiz = self.quiz._create_quiz_copy(user)
            new_unit = LearningUnit.objects.create(
                order=self.order, type="quiz", quiz=new_quiz)
        else:
            new_lesson = self.lesson._create_lesson_copy(user)
            new_unit = LearningUnit.objects.create(
                order=self.order, type="lesson", lesson=new_lesson)
        return new_unit

    def __str__(self):
        name = None
        if self.type == 'lesson':
            name = self.lesson.name
        else:
            name = self.quiz.description
        return name


###############################################################################
class LearningModule(models.Model):
    """ Learning Module to maintain learning units"""
    learning_unit = models.ManyToManyField(LearningUnit,
                                           related_name="learning_unit")
    name = models.CharField(max_length=255)
    description = models.TextField(default=None, null=True, blank=True)
    order = models.IntegerField(default=0)
    creator = models.ForeignKey(User, related_name="module_creator",
                                on_delete=models.CASCADE)
    check_prerequisite = models.BooleanField(default=False)
    check_prerequisite_passes = models.BooleanField(default=False)
    html_data = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)

    def get_quiz_units(self):
        return [unit.quiz for unit in self.learning_unit.filter(
                type="quiz")]

    def get_lesson_units(self):
        return [unit.lesson for unit in self.learning_unit.filter(
                type="lesson").order_by("order")]

    def get_learning_units(self):
        return self.learning_unit.order_by("order")

    def get_added_quiz_lesson(self):
        learning_units = self.learning_unit.order_by("order")
        added_quiz_lessons = []
        if learning_units.exists():
            for unit in learning_units:
                if unit.type == "quiz":
                    added_quiz_lessons.append(("quiz", unit.quiz))
                else:
                    added_quiz_lessons.append(("lesson", unit.lesson))
        return added_quiz_lessons

    def toggle_check_prerequisite(self):
        self.check_prerequisite = not self.check_prerequisite

    def toggle_check_prerequisite_passes(self):
        self.check_prerequisite_passes = not self.check_prerequisite_passes

    def get_next_unit(self, current_unit_id):
        ordered_units = self.learning_unit.order_by("order")
        ordered_units_ids = list(ordered_units.values_list("id", flat=True))
        current_unit_index = ordered_units_ids.index(current_unit_id)
        next_index = current_unit_index + 1
        if next_index == len(ordered_units_ids):
            next_index = 0
        return ordered_units.get(id=ordered_units_ids[next_index])

    def get_status(self, user, course):
        """ Get module status if completed, inprogress or not attempted"""
        learning_module = course.learning_module.prefetch_related(
            "learning_unit").get(id=self.id)
        ordered_units = learning_module.learning_unit.order_by("order")
        status_list = [unit.get_completion_status(user, course)
                       for unit in ordered_units]

        if not status_list:
            default_status = "no units"
        elif all([status == "completed" for status in status_list]):
            default_status = "completed"
        elif all([status == "not attempted" for status in status_list]):
            default_status = "not attempted"
        else:
            default_status = "inprogress"
        return default_status

    def is_prerequisite_complete(self, user, course):
        """ Check if prerequisite module is completed """
        ordered_modules = course.learning_module.order_by("order")
        ordered_modules_ids = list(ordered_modules.values_list(
            "id", flat=True))
        current_module_index = ordered_modules_ids.index(self.id)
        if current_module_index == 0:
            success = True
        else:
            prev_module = ordered_modules.get(
                id=ordered_modules_ids[current_module_index-1])
            status = prev_module.get_status(user, course)
            if status == "completed":
                success = True
            else:
                success = False
        return success

    def get_passing_status(self, user, course):
        course_status = CourseStatus.objects.filter(user=user, course=course)
        ordered_units = []
        if course_status.exists():
            learning_units_with_quiz = self.learning_unit.filter(
                type='quiz'
            ).order_by("order")
            ordered_units = learning_units_with_quiz.order_by("order")

        if ordered_units:
            statuses = [
                unit.quiz.get_answerpaper_passing_status(user, course)
                for unit in ordered_units
            ]
        else:
            statuses = []

        if not statuses:
            status = False
        else:
            status = all(statuses)
        return status

    def is_prerequisite_passed(self, user, course):
        """ Check if prerequisite module is passed """
        ordered_modules = course.learning_module.order_by("order")
        if ordered_modules.first() == self:
            return True
        else:
            if self.order == 0:
                return True
            prev_module = ordered_modules.get(order=self.order-1)
            status = prev_module.get_passing_status(user, course)
            return status

    def has_prerequisite(self):
        return self.check_prerequisite

    def get_module_complete_percent(self, course, user):
        units = self.get_learning_units()
        if not units:
            percent = 0.0
        else:
            status_list = [unit.get_completion_status(user, course)
                           for unit in units]
            count = status_list.count("completed")
            percent = round((count / units.count()) * 100)
        return percent

    def _create_module_copy(self, user, module_name=None):
        learning_units = self.learning_unit.order_by("order")
        new_module = self
        new_module.id = None
        new_module.creator = user
        if module_name:
            new_module.name = module_name
        new_module.save()
        for unit in learning_units:
            new_unit = unit._create_unit_copy(user)
            new_module.learning_unit.add(new_unit)
        return new_module

    def _add_module_to_zip(self, course, zip_file, path):
        module_name = self.name.replace(" ", "_")
        course_name = course.name.replace(" ", "_")
        folder_name = os.sep.join((course_name, module_name))
        lessons = self.get_lesson_units()

        units = self.get_learning_units()
        for idx, unit in enumerate(units):
            next_unit = units[(idx + 1) % len(units)]
            if unit.type == 'lesson':
                unit.lesson._add_lesson_to_zip(next_unit,
                                               self,
                                               course,
                                               zip_file,
                                               path)
            else:
                unit.quiz._add_quiz_to_zip(next_unit,
                                           self,
                                           course,
                                           zip_file,
                                           path)

        module_file_path = os.sep.join((
            path, "templates", "yaksh", "download_course_templates",
            "module.html"
            ))
        module_data = {"course": course, "module": self, "units": units}
        write_templates_to_zip(zip_file, module_file_path, module_data,
                               module_name, folder_name)

    def get_unit_order(self, type, unit):
        if type == "lesson":
            order = self.get_learning_units().get(
                type=type, lesson=unit).order
        else:
            order = self.get_learning_units().get(
                type=type, quiz=unit).order
        return order

    def __str__(self):
        return self.name


###############################################################################
class Course(models.Model):
    """ Course for students"""
    name = models.CharField(max_length=128)
    enrollment = models.CharField(max_length=32, choices=enrollment_methods)
    active = models.BooleanField(default=True)
    code = models.CharField(max_length=128, null=True, blank=True)
    hidden = models.BooleanField(default=False)
    creator = models.ForeignKey(User, related_name='creator',
                                on_delete=models.CASCADE)
    students = models.ManyToManyField(User, related_name='students')
    requests = models.ManyToManyField(User, related_name='requests')
    rejected = models.ManyToManyField(User, related_name='rejected')
    created_on = models.DateTimeField(auto_now_add=True)
    teachers = models.ManyToManyField(User, related_name='teachers')
    is_trial = models.BooleanField(default=False)
    instructions = models.TextField(default=None, null=True, blank=True)
    view_grade = models.BooleanField(default=False)
    learning_module = models.ManyToManyField(LearningModule,
                                             related_name='learning_module')

    # The start date of the course enrollment.
    start_enroll_time = models.DateTimeField(
        "Start Date and Time for enrollment of course",
        default=timezone.now,
        null=True
    )

    # The end date and time of the course enrollment
    end_enroll_time = models.DateTimeField(
        "End Date and Time for enrollment of course",
        default=datetime(
            2199, 1, 1,
            tzinfo=pytz.timezone(timezone.get_current_timezone_name())
        ),
        null=True
    )

    grading_system = models.ForeignKey(GradingSystem, null=True, blank=True,
                                       on_delete=models.CASCADE)

    objects = CourseManager()

    def _create_duplicate_instance(self, creator, course_name=None):
        new_course = self
        new_course.id = None
        new_course.name = course_name if course_name else self.name
        new_course.creator = creator
        new_course.save()
        return new_course

    def create_duplicate_course(self, user):
        learning_modules = self.learning_module.order_by("order")
        copy_course_name = "Copy Of {0}".format(self.name)
        new_course = self._create_duplicate_instance(user, copy_course_name)
        for module in learning_modules:
            copy_module_name = module.name
            new_module = module._create_module_copy(user)
            new_course.learning_module.add(new_module)
        return new_course

    def request(self, *users):
        self.requests.add(*users)

    def get_requests(self):
        return self.requests.all()

    def is_active_enrollment(self):
        return self.start_enroll_time <= timezone.now() < self.end_enroll_time

    def enroll(self, was_rejected, *users):
        self.students.add(*users)
        if not was_rejected:
            self.requests.remove(*users)
        else:
            self.rejected.remove(*users)

    def get_enrolled(self):
        return self.students.all()

    def reject(self, was_enrolled, *users):
        self.rejected.add(*users)
        if not was_enrolled:
            self.requests.remove(*users)
        else:
            self.students.remove(*users)

    def get_rejected(self):
        return self.rejected.all()

    def is_enrolled(self, user):
        return self.students.filter(id=user.id).exists()

    def is_creator(self, user):
        return self.creator == user

    def is_teacher(self, user):
        return self.teachers.filter(id=user.id).exists()

    def is_self_enroll(self):
        return True if self.enrollment == enrollment_methods[1][0] else False

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def add_teachers(self, *teachers):
        self.teachers.add(*teachers)

    def get_teachers(self):
        return self.teachers.all()

    def remove_teachers(self, *teachers):
        self.teachers.remove(*teachers)

    def create_demo(self, user):
        course = Course.objects.filter(creator=user,
                                       name="Yaksh Demo course").exists()
        if not course:
            course = Course.objects.create(name="Yaksh Demo course",
                                           enrollment="open",
                                           creator=user)
            quiz = Quiz()
            demo_quiz = quiz.create_demo_quiz(user)
            demo_ques = Question()
            demo_ques.create_demo_questions(user)
            demo_que_ppr = QuestionPaper()
            demo_que_ppr.create_demo_quiz_ppr(demo_quiz, user)
            success = True
            file_path = os.sep.join(
                (os.path.dirname(__file__), "templates", "yaksh",
                 "demo_video.html")
                )
            rendered_text = render_template(file_path)
            lesson_data = "Demo Lesson\n{0}".format(rendered_text)
            demo_lesson = Lesson.objects.create(
                name="Demo Lesson", description=lesson_data,
                html_data=lesson_data, creator=user
                )
            quiz_unit = LearningUnit.objects.create(
                order=1, type="quiz", quiz=demo_quiz, check_prerequisite=False
                )
            lesson_unit = LearningUnit.objects.create(
                order=2, type="lesson", lesson=demo_lesson,
                check_prerequisite=False
                )
            learning_module = LearningModule.objects.create(
                name="Demo Module", description="<center>Demo Module</center>",
                creator=user, html_data="<center>Demo Module</center>",
                check_prerequisite=False
                )
            learning_module.learning_unit.add(quiz_unit)
            learning_module.learning_unit.add(lesson_unit)
            course.learning_module.add(learning_module)
        else:
            success = False
        return success

    def get_only_students(self):
        teachers = list(self.teachers.values_list("id", flat=True))
        teachers.append(self.creator.id)
        students = self.students.exclude(id__in=teachers)
        return students

    def get_learning_modules(self):
        return self.learning_module.filter(is_trial=False).order_by("order")

    def get_learning_module(self, quiz):
        modules = self.get_learning_modules()
        for module in modules:
            for unit in module.get_learning_units():
                if unit.quiz == quiz:
                    break
        return module

    def get_unit_completion_status(self, module, user, unit):
        course_module = self.learning_module.get(id=module.id)
        learning_unit = course_module.learning_unit.get(id=unit.id)
        return learning_unit.get_completion_status(user, self)

    def get_quizzes(self):
        learning_modules = self.learning_module.all()
        quiz_list = []
        for module in learning_modules:
            quiz_list.extend(module.get_quiz_units())
        return quiz_list

    def get_quiz_details(self):
        return [(quiz, quiz.get_total_students(self),
                 quiz.get_passed_students(self),
                 quiz.get_failed_students(self))
                for quiz in self.get_quizzes()]

    def get_learning_units(self):
        learning_modules = self.learning_module.all()
        learning_units = []
        for module in learning_modules:
            learning_units.extend(module.get_learning_units())
        return learning_units

    def get_lesson_posts(self):
        learning_units = self.get_learning_units()
        comments = []
        for unit in learning_units:
            if unit.lesson is not None:
                lesson_ct = ContentType.objects.get_for_model(unit.lesson)
                title = unit.lesson.name
                try:
                    post = Post.objects.get(
                        target_ct=lesson_ct,
                        target_id=unit.lesson.id,
                        active=True, title=title
                    )
                except Post.DoesNotExist:
                    post = None
                if post is not None:
                    comments.append(post)
        return comments

    def remove_trial_modules(self):
        learning_modules = self.learning_module.all()
        for module in learning_modules:
            module.learning_unit.all().delete()
        learning_modules.delete()

    def is_last_unit(self, module, unit_id):
        last_unit = module.get_learning_units().last()
        return unit_id == last_unit.id

    def next_module(self, current_module_id):
        modules = self.get_learning_modules()
        module_ids = list(modules.values_list("id", flat=True))
        current_unit_index = module_ids.index(current_module_id)
        next_index = current_unit_index + 1
        if next_index == len(module_ids):
            next_index = 0
        return modules.get(id=module_ids[next_index])

    def percent_completed(self, user, modules):
        if not modules:
            percent = 0.0
        else:
            status_list = [module.get_module_complete_percent(self, user)
                           for module in modules]
            count = sum(status_list)
            percent = round((count / modules.count()))
        return percent

    def get_grade(self, user):
        course_status = CourseStatus.objects.filter(course=self, user=user)
        if course_status.exists():
            grade = course_status.first().get_grade()
        else:
            grade = "NA"
        return grade

    def get_current_unit(self, user):
        course_status = CourseStatus.objects.filter(course=self, user_id=user)
        if course_status.exists():
            return course_status.first().current_unit

    def days_before_start(self):
        """ Get the days remaining for the start of the course """
        if timezone.now() < self.start_enroll_time:
            remaining_days = (self.start_enroll_time - timezone.now()).days + 1
        else:
            remaining_days = 0
        return remaining_days

    def get_completion_percent(self, user):
        course_status = CourseStatus.objects.filter(course=self, user=user)
        if course_status.exists():
            percentage = course_status.first().percent_completed
        else:
            percentage = 0
        return percentage

    def is_student(self, user):
        return self.students.filter(id=user.id).exists()

    def create_zip(self, path, static_files):
        zip_file_name = string_io()
        with zipfile.ZipFile(zip_file_name, "a") as zip_file:
            course_name = self.name.replace(" ", "_")
            modules = self.get_learning_modules()
            file_path = os.sep.join(
                (
                    path, "templates", "yaksh",
                    "download_course_templates", "index.html"
                )
            )
            write_static_files_to_zip(zip_file, course_name, path,
                                      static_files)
            course_data = {"course": self, "modules": modules}
            write_templates_to_zip(zip_file, file_path, course_data,
                                   "index", course_name)
            for module in modules:
                module._add_module_to_zip(self, zip_file, path)
        return zip_file_name

    def has_lessons(self):
        modules = self.get_learning_modules()
        status = False
        for module in modules:
            if module.get_lesson_units():
                status = True
                break
        return status

    def __str__(self):
        return self.name


###############################################################################
class CourseStatus(models.Model):
    completed_units = models.ManyToManyField(LearningUnit,
                                             related_name="completed_units")
    current_unit = models.ForeignKey(LearningUnit, related_name="current_unit",
                                     null=True, blank=True,
                                     on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    grade = models.CharField(max_length=255, null=True, blank=True)
    percentage = models.FloatField(default=0.0)
    percent_completed = models.IntegerField(default=0)

    def get_grade(self):
        return self.grade

    def set_grade(self):
        if self.is_course_complete():
            self.calculate_percentage()
            if self.course.grading_system is None:
                grading_system = GradingSystem.objects.get(
                    name__contains='default'
                )
            else:
                grading_system = self.course.grading_system
            grade = grading_system.get_grade(self.percentage)
            self.grade = grade
            self.save()

    def calculate_percentage(self):
        quizzes = self.course.get_quizzes()
        if self.is_course_complete() and quizzes:
            total_weightage = 0
            sum = 0
            for quiz in quizzes:
                total_weightage += quiz.weightage
                marks = AnswerPaper.objects.get_user_best_of_attempts_marks(
                        quiz, self.user.id, self.course.id)
                out_of = quiz.questionpaper_set.first().total_marks
                sum += (marks/out_of)*quiz.weightage
            self.percentage = (sum/total_weightage)*100
            self.save()

    def is_course_complete(self):
        modules = self.course.get_learning_modules()
        complete = False
        for module in modules:
            complete = module.get_status(self.user, self.course) == 'completed'
            if not complete:
                break
        return complete

    def set_current_unit(self, unit):
        self.current_unit = unit
        self.save()

    def __str__(self):
        return "{0} status for {1}".format(
            self.course.name, self.user.username
        )


###############################################################################
class ConcurrentUser(models.Model):
    concurrent_user = models.OneToOneField(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)


###############################################################################
class Profile(models.Model):
    """Profile for a user to store roll number and other details."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20)
    institute = models.CharField(max_length=128)
    department = models.CharField(max_length=64)
    position = models.CharField(max_length=64)
    is_moderator = models.BooleanField(default=False)
    timezone = models.CharField(
        max_length=64,
        default=pytz.utc.zone,
        choices=[(tz, tz) for tz in pytz.common_timezones]
    )
    is_email_verified = models.BooleanField(default=False)
    activation_key = models.CharField(max_length=255, blank=True, null=True)
    key_expiry_time = models.DateTimeField(blank=True, null=True)

    def get_user_dir(self):
        """Return the output directory for the user."""

        user_dir = join(settings.OUTPUT_DIR, str(self.user.id))
        if not exists(user_dir):
            os.makedirs(user_dir)
            os.chmod(user_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        return user_dir

    def get_moderated_courses(self):
        return Course.objects.filter(teachers=self.user)

    def _toggle_moderator_group(self, group_name):
        group = Group.objects.get(name=group_name)
        if self.is_moderator:
            self.user.groups.add(group)
        else:
            self.user.groups.remove(group)
            for course in self.get_moderated_courses():
                course.remove_teachers(self.user)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            old_profile = Profile.objects.get(pk=self.pk)
            if old_profile.is_moderator != self.is_moderator:
                self._toggle_moderator_group(group_name=MOD_GROUP_NAME)
        super(Profile, self).save(*args, **kwargs)

    def __str__(self):
        return '%s' % (self.user.get_full_name() or self.user.username)


###############################################################################
class Question(models.Model):
    """Question for a quiz."""

    # A one-line summary of the question.
    summary = models.CharField(max_length=256)

    # The question text, should be valid HTML.
    description = models.TextField()

    # Number of points for the question.
    points = models.FloatField(default=1.0)

    # The language for question.
    language = models.CharField(max_length=24,
                                choices=languages)

    topic = models.CharField(max_length=50, blank=True, null=True)

    # The type of question.
    type = models.CharField(max_length=24, choices=question_types)

    # Is this question active or not. If it is inactive it will not be used
    # when creating a QuestionPaper.
    active = models.BooleanField(default=True)

    # Tags for the Question.
    tags = TaggableManager(blank=True)

    # Snippet of code provided to the user.
    snippet = models.TextField(blank=True)

    # user for particular question
    user = models.ForeignKey(User, related_name="user",
                             on_delete=models.CASCADE)

    # Does this question allow partial grading
    partial_grading = models.BooleanField(default=False)

    # Check assignment upload based question
    grade_assignment_upload = models.BooleanField(default=False)

    min_time = models.IntegerField("time in minutes", default=0)

    # Solution for the question.
    solution = models.TextField(blank=True)

    content = GenericRelation(
        "TableOfContents", related_query_name='questions'
    )

    tc_code_types = {
        "python": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "c": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "cpp": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "java": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "r": [
            ("standardtestcase", "Standard TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "bash": [
            ("standardtestcase", "Standard TestCase"),
            ("stdiobasedtestcase", "StdIO TestCase"),
            ("hooktestcase", "Hook TestCase")
        ],
        "scilab": [
            ("standardtestcase", "Standard TestCase"),
            ("hooktestcase", "Hook TestCase")
        ]
    }

    def consolidate_answer_data(self, user_answer, user=None, regrade=False):
        question_data = {}
        metadata = {}
        test_case_data = []
        test_cases = self.get_test_cases()

        for test in test_cases:
            test_case_as_dict = test.get_field_value()
            test_case_data.append(test_case_as_dict)

        question_data['test_case_data'] = test_case_data
        metadata['user_answer'] = user_answer
        metadata['language'] = self.language
        metadata['partial_grading'] = self.partial_grading
        files = FileUpload.objects.filter(question=self)
        if files:
            if settings.USE_AWS:
                metadata['file_paths'] = [
                    (file.file.url, file.extract)
                     for file in files
                ]
            else:
                metadata['file_paths'] = [
                    (self.get_file_url(file.file.url), file.extract)
                     for file in files
                ]
        if self.type == "upload" and regrade:
            file = AssignmentUpload.objects.only(
                "assignmentFile").filter(
                assignmentQuestion_id=self.id, answer_paper__user_id=user.id
                ).order_by("-id").first()
            if file:
                if settings.USE_AWS:
                    metadata['assign_files'] = [file.assignmentFile.url]
                else:
                    metadata['assign_files'] = [
                        self.get_file_url(file.assignmentFile.url)
                    ]
        question_data['metadata'] = metadata
        return json.dumps(question_data)

    def get_file_url(self, path):
        return f'{settings.DOMAIN_HOST}{path}'

    def dump_questions(self, question_ids, user):
        questions = Question.objects.filter(id__in=question_ids,
                                            user_id=user.id, active=True
                                            )
        questions_dict = []
        zip_file_name = string_io()
        zip_file = zipfile.ZipFile(zip_file_name, "a")
        for question in questions:
            test_case = question.get_test_cases()
            file_names = question._add_and_get_files(zip_file)
            q_dict = model_to_dict(question, exclude=['id', 'user'])
            testcases = []
            for case in test_case:
                testcases.append(case.get_field_value())
            q_dict['testcase'] = testcases
            q_dict['files'] = file_names
            q_dict['tags'] = [tag.name for tag in q_dict['tags']]
            questions_dict.append(q_dict)
        question._add_yaml_to_zip(zip_file, questions_dict)
        return zip_file_name

    def load_questions(self, questions_list, user, file_path=None,
                       files_list=None):
        try:
            questions = ruamel.yaml.safe_load_all(questions_list)
            msg = "Questions Uploaded Successfully"
            for question in questions:
                question['user'] = user
                file_names = question.pop('files') \
                    if 'files' in question else None
                tags = question.pop('tags') if 'tags' in question else None
                test_cases = question.pop('testcase')
                que, result = Question.objects.get_or_create(**question)
                if file_names and file_path:
                    que._add_files_to_db(file_names, file_path)
                if tags:
                    que.tags.add(*tags)
                for test_case in test_cases:
                    try:
                        test_case_type = test_case.pop('test_case_type')
                        model_class = get_model_class(test_case_type)
                        new_test_case, obj_create_status = \
                            model_class.objects.get_or_create(
                                question=que, **test_case
                            )
                        new_test_case.type = test_case_type
                        new_test_case.save()

                    except Exception:
                        msg = "Unable to parse test case data"
        except Exception as exc_msg:
            msg = "Error Parsing Yaml: {0}".format(exc_msg)
        return msg

    def get_test_cases(self, **kwargs):
        tc_list = []
        for tc in self.testcase_set.values_list("type", flat=True).distinct():
            test_case_ctype = ContentType.objects.get(app_label="yaksh",
                                                      model=tc)
            test_case = test_case_ctype.get_all_objects_for_this_type(
                question=self,
                **kwargs
            )
            tc_list.extend(test_case)
        return tc_list

    def get_test_cases_as_dict(self, **kwargs):
        tc_list = []
        for tc in self.testcase_set.values_list("type", flat=True).distinct():
            test_case_ctype = ContentType.objects.get(app_label="yaksh",
                                                      model=tc)
            test_case = test_case_ctype.get_all_objects_for_this_type(
                question=self,
                **kwargs
            )
            for tc in test_case:
                tc_list.append(model_to_dict(tc))
            return tc_list

    def get_test_case(self, **kwargs):
        for tc in self.testcase_set.all():
            test_case_type = tc.type
            test_case_ctype = ContentType.objects.get(
                app_label="yaksh",
                model=test_case_type
            )
            test_case = test_case_ctype.get_object_for_this_type(
                question=self,
                **kwargs
            )

        return test_case

    def get_ordered_test_cases(self, answerpaper):
        try:
            order = TestCaseOrder.objects.get(answer_paper=answerpaper,
                                              question=self
                                              ).order.split(",")
            return [self.get_test_case(id=int(tc_id))
                    for tc_id in order
                    ]
        except TestCaseOrder.DoesNotExist:
            return self.get_test_cases()

    def get_maximum_test_case_weight(self, **kwargs):
        max_weight = 0.0
        for test_case in self.get_test_cases():
            max_weight += test_case.weight

        return max_weight

    def _add_and_get_files(self, zip_file):
        files = FileUpload.objects.filter(question=self)
        files_list = []
        for f in files:
            zip_file.writestr(
                os.path.join("additional_files", os.path.basename(f.file.name)),
                f.file.read()
            )
            files_list.append(((os.path.basename(f.file.name)), f.extract))
        return files_list

    def _add_files_to_db(self, file_names, path):
        for file_name, extract in file_names:
            q_file = glob.glob(os.path.join(path, "**", file_name))[0]
            if os.path.exists(q_file):
                que_file = open(q_file, 'rb')
                # Converting to Python file object with
                # some Django-specific additions
                django_file = File(que_file)
                file_upload = FileUpload()
                file_upload.question = self
                file_upload.extract = extract
                file_upload.file.save(file_name, django_file, save=True)

    def _add_yaml_to_zip(self, zip_file, q_dict, path_to_file=None):
        tmp_file_path = tempfile.mkdtemp()
        yaml_path = os.path.join(tmp_file_path, "questions_dump.yaml")
        for elem in q_dict:
            relevant_dict = CommentedMap()
            relevant_dict['summary'] = elem.pop('summary')
            relevant_dict['type'] = elem.pop('type')
            relevant_dict['language'] = elem.pop('language')
            relevant_dict['description'] = elem.pop('description')
            relevant_dict['points'] = elem.pop('points')
            relevant_dict['testcase'] = elem.pop('testcase')
            relevant_dict.update(CommentedMap(sorted(elem.items(),
                                                     key=lambda x: x[0]
                                                     ))
                                 )

            yaml_block = dict_to_yaml(relevant_dict)
            with open(yaml_path, "a") as yaml_file:
                yaml_file.write(yaml_block)
        zip_file.write(yaml_path, os.path.basename(yaml_path))
        zip_file.close()
        shutil.rmtree(tmp_file_path)

    def read_yaml(self, file_path, user, files=None):
        msg = "Failed to upload Questions"
        for ext in ["yaml", "yml"]:
            for yaml_file in glob.glob(os.path.join(file_path,
                                                    "*.{0}".format(ext)
                                                    )):
                if os.path.exists(yaml_file):
                    with open(yaml_file, 'r') as q_file:
                        questions_list = q_file.read()
                        msg = self.load_questions(questions_list, user,
                                                  file_path, files
                                                  )

        if files:
            delete_files(files, file_path)
        return msg

    def create_demo_questions(self, user):
        zip_file_path = os.path.join(
            FIXTURES_DIR_PATH, 'demo_questions.zip'
        )
        files, extract_path = extract_files(zip_file_path)
        self.read_yaml(extract_path, user, files)

    def get_test_case_options(self):
        options = None
        if self.type == "code":
            options = self.tc_code_types.get(self.language)
        elif self.type == "mcq" or self.type == "mcc":
            options = [("mcqtestcase", "Mcq TestCase")]
        elif self.type == "integer":
            options = [("integertestcase", "Integer TestCase")]
        elif self.type == "float":
            options = [("floattestcase", "Float TestCase")]
        elif self.type == "string":
            options = [("stringtestcase", "String TestCase")]
        elif self.type == "arrange":
            options = [("arrangetestcase", "Arrange TestCase")]
        elif self.type == "upload":
            options = [("hooktestcase", "Hook TestCase")]
        return options

    def __str__(self):
        return self.summary


###############################################################################
class FileUpload(models.Model):
    file = models.FileField(upload_to=get_upload_dir, blank=True)
    question = models.ForeignKey(Question, related_name="question",
                                 on_delete=models.CASCADE)
    extract = models.BooleanField(default=False)
    hide = models.BooleanField(default=False)

    def set_extract_status(self):
        if self.extract:
            self.extract = False
        else:
            self.extract = True
        self.save()

    def toggle_hide_status(self):
        if self.hide:
            self.hide = False
        else:
            self.hide = True
        self.save()

    def get_filename(self):
        return os.path.basename(self.file.name)

pre_delete.connect(file_cleanup, sender=FileUpload)
###############################################################################
class Answer(models.Model):
    """Answers submitted by the users."""

    # The question for which user answers.
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # The answer submitted by the user.
    answer = models.TextField(null=True, blank=True)

    # Error message when auto-checking the answer.
    error = models.TextField()

    # Marks obtained for the answer. This can be changed by the teacher if the
    # grading is manual.
    marks = models.FloatField(default=0.0)

    # Is the answer correct.
    correct = models.BooleanField(default=False)

    # Whether skipped or not.
    skipped = models.BooleanField(default=False)

    comment = models.TextField(null=True, blank=True)

    def set_marks(self, marks):
        if marks > self.question.points:
            self.marks = self.question.points
        else:
            self.marks = marks

    def set_comment(self, comments):
        self.comment = comments

    def __str__(self):
        return "Answer for question {0}".format(self.question.summary)


###############################################################################
class QuestionPaperManager(models.Manager):

    def _create_trial_from_questionpaper(self, original_quiz_id):
        """Creates a copy of the original questionpaper"""
        trial_questionpaper = self.get(quiz_id=original_quiz_id)
        fixed_ques = trial_questionpaper.get_ordered_questions()
        trial_questions = {"fixed_questions": fixed_ques,
                           "random_questions": trial_questionpaper
                           .random_questions.all()
                           }
        trial_questionpaper.pk = None
        trial_questionpaper.save()
        return trial_questionpaper, trial_questions

    def create_trial_paper_to_test_questions(self, trial_quiz,
                                             questions_list):
        """Creates a trial question paper to test selected questions"""
        if questions_list is not None:
            trial_questionpaper = self.create(quiz=trial_quiz,
                                              total_marks=10,
                                              )
            trial_questionpaper.fixed_question_order = ",".join(questions_list)
            trial_questionpaper.fixed_questions.add(*questions_list)
            return trial_questionpaper

    def create_trial_paper_to_test_quiz(self, trial_quiz, original_quiz_id):
        """Creates a trial question paper to test quiz."""
        if self.filter(quiz=trial_quiz).exists():
            self.get(quiz=trial_quiz).delete()
        trial_questionpaper, trial_questions = \
            self._create_trial_from_questionpaper(original_quiz_id)
        trial_questionpaper.quiz = trial_quiz
        trial_questionpaper.fixed_questions\
            .add(*trial_questions["fixed_questions"])
        trial_questionpaper.random_questions\
            .add(*trial_questions["random_questions"])
        trial_questionpaper.save()
        return trial_questionpaper


###############################################################################
class QuestionPaper(models.Model):
    """Question paper stores the detail of the questions."""

    # Question paper belongs to a particular quiz.
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)

    # Questions that will be mandatory in the quiz.
    fixed_questions = models.ManyToManyField(Question)

    # Questions that will be fetched randomly from the Question Set.
    random_questions = models.ManyToManyField("QuestionSet")

    # Option to shuffle questions, each time a new question paper is created.
    shuffle_questions = models.BooleanField(default=False, blank=False)

    # Total marks for the question paper.
    total_marks = models.FloatField(default=0.0, blank=True)

    # Sequence or Order of fixed questions
    fixed_question_order = models.TextField(blank=True)

    # Shuffle testcase order.
    shuffle_testcases = models.BooleanField("Shuffle testcase for each user",
                                            default=True
                                            )

    objects = QuestionPaperManager()

    def get_question_bank(self):
        ''' Gets all the questions in the question paper'''
        questions = list(self.fixed_questions.all())
        for random_set in self.random_questions.all():
            questions += list(random_set.questions.all())
        return questions

    def _create_duplicate_questionpaper(self, quiz):
        new_questionpaper = QuestionPaper.objects.create(
            quiz=quiz, shuffle_questions=self.shuffle_questions,
            total_marks=self.total_marks,
            fixed_question_order=self.fixed_question_order
        )
        new_questionpaper.fixed_questions.add(*self.fixed_questions.all())
        new_questionpaper.random_questions.add(*self.random_questions.all())

        return new_questionpaper

    def update_total_marks(self):
        """ Updates the total marks for the Question Paper"""
        marks = 0.0
        questions = self.fixed_questions.all()
        for question in questions:
            marks += question.points
        for question_set in self.random_questions.all():
            question_set.marks = question_set.questions.first().points
            question_set.save()
            marks += question_set.marks * question_set.num_questions
        self.total_marks = marks
        self.save()

    def _get_questions_for_answerpaper(self):
        """ Returns fixed and random questions for the answer paper"""
        questions = self.get_ordered_questions()
        for question_set in self.random_questions.all():
            questions += question_set.get_random_questions()
        if self.shuffle_questions:
            all_questions = self.get_shuffled_questions(questions)
        else:
            all_questions = questions
        return all_questions

    def make_answerpaper(self,
                         user, ip, attempt_num, course_id, special=False):
        """Creates an answer paper for the user to attempt the quiz"""
        try:
            ans_paper = AnswerPaper.objects.get(user=user,
                                                attempt_number=attempt_num,
                                                question_paper=self,
                                                course_id=course_id
                                                )
        except AnswerPaper.DoesNotExist:
            ans_paper = AnswerPaper(
                user=user,
                user_ip=ip,
                attempt_number=attempt_num,
                course_id=course_id
            )
            ans_paper.start_time = timezone.now()
            ans_paper.end_time = ans_paper.start_time + \
                timedelta(minutes=self.quiz.duration)
            ans_paper.question_paper = self
            ans_paper.is_special = special
            ans_paper.save()
            questions = self._get_questions_for_answerpaper()
            ans_paper.questions.add(*questions)
            question_ids = []
            for question in questions:
                question_ids.append(str(question.id))
                if (question.type == "arrange") or (
                        self.shuffle_testcases and
                        question.type in ["mcq", "mcc"]):
                    testcases = question.get_test_cases()
                    random.shuffle(testcases)
                    testcases_ids = ",".join([str(tc.id) for tc in testcases]
                                             )
                    if not TestCaseOrder.objects.filter(
                         answer_paper=ans_paper, question=question
                         ).exists():
                        TestCaseOrder.objects.create(
                            answer_paper=ans_paper, question=question,
                            order=testcases_ids)

            ans_paper.questions_order = ",".join(question_ids)
            ans_paper.save()
            ans_paper.questions_unanswered.add(*questions)
        return ans_paper

    def _is_attempt_allowed(self, user, course_id):
        attempts = AnswerPaper.objects.get_total_attempt(questionpaper=self,
                                                         user=user,
                                                         course_id=course_id)
        attempts_allowed = attempts < self.quiz.attempts_allowed
        infinite_attempts = self.quiz.attempts_allowed == -1
        return attempts_allowed or infinite_attempts

    def can_attempt_now(self, user, course_id):
        if self._is_attempt_allowed(user, course_id):
            last_attempt = AnswerPaper.objects.get_user_last_attempt(
                user=user, questionpaper=self, course_id=course_id
            )
            if last_attempt:
                time_lag = (timezone.now() - last_attempt.start_time)
                time_lag = time_lag.total_seconds()/3600
                can_attempt = time_lag >= self.quiz.time_between_attempts
                msg = "You cannot start the next attempt for this quiz before"\
                    "{0} hour(s)".format(self.quiz.time_between_attempts) \
                    if not can_attempt else None
                return can_attempt, msg
            else:
                return True, None
        else:
            msg = "You cannot attempt {0} quiz more than {1} time(s)".format(
                self.quiz.description, self.quiz.attempts_allowed
            )
            return False, msg

    def create_demo_quiz_ppr(self, demo_quiz, user):
        question_paper = QuestionPaper.objects.create(quiz=demo_quiz,
                                                      shuffle_questions=False
                                                      )
        summaries = ['Find the value of n', 'Print Output in Python2.x',
                     'Adding decimals', 'For Loop over String',
                     'Hello World in File',
                     'Arrange code to convert km to miles',
                     'Print Hello, World!', "Square of two numbers",
                     'Check Palindrome', 'Add 3 numbers', 'Reverse a string'
                     ]
        questions = Question.objects.filter(active=True,
                                            summary__in=summaries,
                                            user=user)
        q_order = [str(que.id) for que in questions]
        question_paper.fixed_question_order = ",".join(q_order)
        question_paper.save()
        # add fixed set of questions to the question paper
        question_paper.fixed_questions.add(*questions)
        question_paper.update_total_marks()
        question_paper.save()

    def get_ordered_questions(self):
        ques = []
        if self.fixed_question_order:
            que_order = self.fixed_question_order.split(',')
            for que_id in que_order:
                ques.append(self.fixed_questions.get(id=que_id))
        else:
            ques = list(self.fixed_questions.all())
        return ques

    def get_shuffled_questions(self, questions):
        """Get shuffled questions if auto suffle is enabled"""
        random.shuffle(questions)
        return questions

    def has_questions(self):
        questions = self.get_ordered_questions() + \
                    list(self.random_questions.all())
        return len(questions) > 0

    def get_questions_count(self):
        que_count = self.fixed_questions.count()
        for r_set in self.random_questions.all():
            que_count += r_set.num_questions
        return que_count

    def __str__(self):
        return "Question Paper for " + self.quiz.description


###############################################################################
class QuestionSet(models.Model):
    """Question set contains a set of questions from which random questions
       will be selected for the quiz.
    """

    # Marks of each question of a particular Question Set
    marks = models.FloatField()

    # Number of questions to be fetched for the quiz.
    num_questions = models.IntegerField()

    # Set of questions for sampling randomly.
    questions = models.ManyToManyField(Question)

    def get_random_questions(self):
        """ Returns random questions from set of questions"""
        return sample(list(self.questions.all()), self.num_questions)


###############################################################################
class AnswerPaperManager(models.Manager):

    def get_attempt_numbers(self, questionpaper_id, course_id,
                            status='completed'):
        ''' Return list of attempt numbers'''
        attempt_numbers = self.filter(
            question_paper_id=questionpaper_id, status=status,
            course_id=course_id
        ).values_list('attempt_number', flat=True).distinct()
        return attempt_numbers

    def has_attempt(self, questionpaper_id, attempt_number, course_id,
                    status='completed'):
        ''' Whether question paper is attempted'''
        return self.filter(
            question_paper_id=questionpaper_id,
            attempt_number=attempt_number, status=status,
            course_id=course_id
        ).exists()

    def get_count(self, questionpaper_id, attempt_number, course_id,
                  status='completed'):
        ''' Return count of answerpapers for a specfic question paper
            and attempt number'''
        return self.filter(
            question_paper_id=questionpaper_id,
            attempt_number=attempt_number, status=status,
            course_id=course_id
        ).count()

    def get_question_statistics(self, questionpaper_id, attempt_number,
                                course_id, status='completed'):
        ''' Return dict with question object as key and list as value
            The list contains four values, first total attempts, second correct
            attempts, third correct percentage, fourth per test case answers
            a question
        '''
        question_stats = {}
        qp = QuestionPaper.objects.get(id=questionpaper_id)
        all_questions = qp.get_question_bank()
        que_ids = [que.id for que in all_questions]
        papers = self.filter(
            question_paper_id=questionpaper_id, course_id=course_id,
            attempt_number=attempt_number, status=status
        ).values_list("id", flat=True)
        answers = Answer.objects.filter(
            answerpaper__id__in=papers, question_id__in=que_ids
        ).order_by("id").values(
            "answerpaper__id", "question_id", "correct", "answer"
        )

        def _get_per_tc_data(answers, q_type):
            tc = []
            for answer in answers["answer"]:
                try:
                    ans = literal_eval(answer) if answer else None
                    tc.extend(ans) if q_type == "mcc" else tc.append(str(ans))
                except Exception:
                    pass
            return dict(Counter(tc))
        df = pd.DataFrame(answers)
        if not df.empty:
            for question in all_questions:
                que = df[df["question_id"] == question.id].groupby(
                        "answerpaper__id").tail(1)
                if not que.empty:
                    total_attempts = que.shape[0]
                    correct_attempts = que[que["correct"] == True].shape[0]
                    per_tc_ans = {}
                    if question.type in ["mcq", "mcc"]:
                        per_tc_ans = _get_per_tc_data(que, question.type)
                    question_stats[question] = (
                        total_attempts, correct_attempts,
                        round((correct_attempts/total_attempts)*100),
                        per_tc_ans
                    )
        return question_stats

    def _get_answerpapers_for_quiz(self, questionpaper_id, course_id,
                                   status=False):
        if not status:
            return self.filter(question_paper_id__in=questionpaper_id,
                               course_id=course_id)
        else:
            return self.filter(question_paper_id__in=questionpaper_id,
                               course_id=course_id,
                               status="completed")

    def _get_answerpapers_users(self, answerpapers):
        return answerpapers.values_list('user', flat=True).distinct()

    def get_latest_attempts(self, questionpaper_id, course_id):
        papers = self._get_answerpapers_for_quiz(questionpaper_id, course_id)
        users = self._get_answerpapers_users(papers)
        latest_attempts = []
        for user in users:
            latest_attempts.append(self._get_latest_attempt(papers, user))
        return latest_attempts

    def _get_latest_attempt(self, answerpapers, user_id):
        return answerpapers.filter(
            user_id=user_id
        ).order_by('-attempt_number')[0]

    def get_user_last_attempt(self, questionpaper, user, course_id):
        attempts = self.filter(question_paper=questionpaper,
                               user=user,
                               course_id=course_id).order_by('-attempt_number')
        if attempts:
            return attempts[0]

    def get_user_answerpapers(self, user):
        return self.filter(user=user)

    def get_total_attempt(self, questionpaper, user, course_id):
        return self.filter(question_paper=questionpaper, user=user,
                           course_id=course_id).count()

    def get_users_for_questionpaper(self, questionpaper_id, course_id):
        return self._get_answerpapers_for_quiz(questionpaper_id, course_id,
                                               status=True)\
            .values("user__id", "user__first_name", "user__last_name")\
            .order_by("user__first_name")\
            .distinct()

    def get_user_all_attempts(self, questionpaper, user, course_id):
        return self.filter(question_paper_id__in=questionpaper, user_id=user,
                           course_id=course_id)\
                            .order_by('-attempt_number')

    def get_user_data(self, user, questionpaper_id, course_id,
                      attempt_number=None):
        if attempt_number is not None:
            papers = self.filter(user_id=user.id,
                                 question_paper_id__in=questionpaper_id,
                                 course_id=course_id,
                                 attempt_number=attempt_number)
        else:
            papers = self.filter(
                user=user, question_paper_id=questionpaper_id,
                course_id=course_id
            ).order_by("-attempt_number")
        data = {}
        profile = user.profile if hasattr(user, 'profile') else None
        data['user'] = user
        data['profile'] = profile
        data['papers'] = papers
        data['questionpaperid'] = questionpaper_id
        return data

    def get_user_best_of_attempts_marks(self, quiz, user_id, course_id):
        best_attempt = 0.0
        papers = self.filter(question_paper__quiz_id=quiz.id,
                             course_id=course_id,
                             user=user_id).order_by("-marks_obtained").values(
                             "marks_obtained")
        if papers.exists():
            best_attempt = papers[0]["marks_obtained"]
        return best_attempt

    def get_user_scores(self, question_papers, user, course_id):
        if not question_papers:
            return None
        qp_ids = list(zip(*question_papers))[0]
        papers = self.filter(
            course_id=course_id, user_id=user.get("id"),
            question_paper__id__in=qp_ids
        ).values("question_paper_id", "marks_obtained")
        df = pd.DataFrame(papers)
        user_marks = 0
        ap_data = None
        if not df.empty:
            ap_data = df.groupby("question_paper_id").tail(1)
        for qp_id, quiz, quiz_marks in question_papers:
            if ap_data is not None:
                qp = ap_data['question_paper_id'].to_list()
                marks = ap_data['marks_obtained'].to_list()
                if qp_id in qp:
                    idx = qp.index(qp_id)
                    user_marks += marks[idx]
                    user[f"{quiz}-{quiz_marks}-Marks"] = marks[idx]
                else:
                    user[f"{quiz}-{quiz_marks}-Marks"] = 0
            else:
                user[f"{quiz}-{quiz_marks}-Marks"] = 0
        user.pop("id")
        user["total_marks"] = user_marks

    def get_questions_attempted(self, answerpaper_ids):
        answers = Answer.objects.filter(
            answerpaper__id__in=answerpaper_ids
        ).values("question_id", "answerpaper__id")
        df = pd.DataFrame(answers)
        if not df.empty and "answerpaper__id" in df.columns:
            answerpapers = df.groupby("answerpaper__id")
            question_attempted = {}
            for ap in answerpapers:
                question_attempted[ap[0]] = len(ap[1]["question_id"].unique())
            return question_attempted


###############################################################################
class AnswerPaper(models.Model):
    """A answer paper for a student -- one per student typically.
    """
    # The user taking this question paper.
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    questions = models.ManyToManyField(Question, related_name='questions')

    # The Quiz to which this question paper is attached to.
    question_paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE)

    # Answepaper will be unique to the course
    course = models.ForeignKey(Course, null=True, on_delete=models.CASCADE)

    # The attempt number for the question paper.
    attempt_number = models.IntegerField()

    # The time when this paper was started by the user.
    start_time = models.DateTimeField()

    # The time when this paper was ended by the user.
    end_time = models.DateTimeField()

    # User's IP which is logged.
    user_ip = models.CharField(max_length=255)

    # The questions unanswered
    questions_unanswered = models.ManyToManyField(
        Question, related_name='questions_unanswered'
    )

    # The questions answered
    questions_answered = models.ManyToManyField(
        Question, related_name='questions_answered'
    )

    # All the submitted answers.
    answers = models.ManyToManyField(Answer)

    # Teacher comments on the question paper.
    comments = models.TextField()

    # Total marks earned by the student in this paper.
    marks_obtained = models.FloatField(null=True, default=0.0)

    # Marks percent scored by the user
    percent = models.FloatField(null=True, default=0.0)

    # Result of the quiz, True if student passes the exam.
    passed = models.BooleanField(null=True)

    # Status of the quiz attempt
    status = models.CharField(
        max_length=20, choices=test_status,
        default='inprogress'
    )

    # set question order
    questions_order = models.TextField(blank=True, default='')

    extra_time = models.FloatField('Additional time in mins', default=0.0)

    is_special = models.BooleanField(default=False)

    objects = AnswerPaperManager()

    class Meta:
        unique_together = ('user', 'question_paper',
                           'attempt_number', "course"
                           )

    def get_per_question_score(self, question_ids):
        if not question_ids:
            return None
        que_ids = list(zip(*question_ids))[1]
        answers = self.answers.filter(
            question_id__in=que_ids).values("question_id", "marks")
        que_data = {}
        df = pd.DataFrame(answers)
        ans_data = None
        if not df.empty:
            ans_data = df.groupby("question_id").tail(1)
        for que_summary, que_id, que_comments in question_ids:
            if ans_data is not None:
                ans = ans_data['question_id'].to_list()
                marks = ans_data['marks'].to_list()
                if que_id in ans:
                    idx = ans.index(que_id)
                    que_data[que_summary] = marks[idx]
                else:
                    que_data[que_summary] = 0
            else:
                que_data[que_summary] = 0
            que_data[que_comments] = "NA"
        return que_data

    def current_question(self):
        """Returns the current active question to display."""
        unanswered_questions = self.questions_unanswered.all()
        if unanswered_questions.exists():
            cur_question = self.get_current_question(unanswered_questions)
        else:
            cur_question = self.get_current_question(self.questions.all())
        return cur_question

    def get_current_question(self, questions):
        if self.questions_order:
            available_question_ids = questions.values_list('id', flat=True)
            ordered_question_ids = [int(q)
                                    for q in self.questions_order.split(',')]
            for qid in ordered_question_ids:
                if qid in available_question_ids:
                    return questions.get(id=qid)
        return questions.first()

    def questions_left(self):
        """Returns the number of questions left."""
        return self.questions_unanswered.count()

    def add_completed_question(self, question_id):
        """
            Adds the completed question to the list of answered
            questions and returns the next question.
        """
        if question_id not in self.questions_answered.all():
            self.questions_answered.add(question_id)
        self.questions_unanswered.remove(question_id)

        return self.next_question(question_id)

    def next_question(self, question_id):
        """
            Skips the current question and returns the next sequentially
             available question.
        """
        if self.questions_order:
            all_questions = [
                int(q_id) for q_id in self.questions_order.split(',')
            ]
        else:
            all_questions = list(self.questions.all().values_list(
                'id', flat=True))
        if len(all_questions) == 0:
            return None
        try:
            index = all_questions.index(int(question_id))
            next_id = all_questions[index+1]
        except (ValueError, IndexError):
            next_id = all_questions[0]
        return self.questions.get(id=next_id)

    def get_all_ordered_questions(self):
        """Get all questions in a specific order for answerpaper"""
        if self.questions_order:
            que_ids = [int(q_id) for q_id in self.questions_order.split(',')]
            questions = [self.questions.get(id=que_id)
                         for que_id in que_ids]
        else:
            questions = list(self.questions.all())
        return questions

    def set_extra_time(self, time=0):
        now = timezone.now()
        self.extra_time += time
        if self.status == 'completed' and self.end_time < now:
            self.extra_time = time
            quiz_time = self.question_paper.quiz.duration
            self.start_time = now - timezone.timedelta(minutes=quiz_time)
            self.end_time = now + timezone.timedelta(minutes=time)
            self.status = 'inprogress'
        self.save()

    def time_left(self):
        """Return the time remaining for the user in seconds."""
        secs = self._get_total_seconds()
        extra_time = self.extra_time * 60
        total = self.question_paper.quiz.duration*60.0
        remain = max(total - (secs - extra_time), 0)
        return int(remain)

    def time_left_on_question(self, question):
        secs = self._get_total_seconds()
        total = question.min_time*60.0
        remain = max(total - secs, 0)
        return int(remain)

    def _get_total_seconds(self):
        dt = timezone.now() - self.start_time
        try:
            secs = dt.total_seconds()
        except AttributeError:
            # total_seconds is new in Python 2.7. :(
            secs = dt.seconds + dt.days*24*3600
        return secs

    def _get_marks_for_question(self, question):
        marks = 0.0
        answers = question.answer_set.filter(answerpaper=self)
        if answers.exists():
            marks = [answer.marks for answer in answers]
            max_marks = max(marks)
            marks = max_marks
        return marks

    def _update_marks_obtained(self):
        """Updates the total marks earned by student for this paper."""
        marks = 0.0
        for question in self.questions.all():
            marks += self._get_marks_for_question(question)
        self.marks_obtained = marks

    def _update_percent(self):
        """Updates the percent gained by the student for this paper."""
        total_marks = self.question_paper.total_marks
        if self.marks_obtained is not None:
            percent = self.marks_obtained/total_marks*100
            self.percent = round(percent, 2)

    def _update_passed(self):
        """
            Checks whether student passed or failed, as per the quiz
            passing criteria.
        """
        if self.percent is not None:
            if self.percent >= self.question_paper.quiz.pass_criteria:
                self.passed = True
            else:
                self.passed = False

    def _update_status(self, state):
        """ Sets status as inprogress or completed """
        self.status = state

    def update_marks(self, state='completed'):
        self._update_marks_obtained()
        self._update_percent()
        self._update_passed()
        self._update_status(state)
        self.save()

    def set_end_time(self, datetime):
        """ Sets end time """
        self.end_time = datetime
        self.save()

    def get_answer_comment(self, question_id):
        answer = self.answers.filter(question_id=question_id).last()
        if answer:
            return answer.comment

    def get_question_answers(self):
        """
            Return a dictionary with keys as questions and a list of the
            corresponding answers.
        """
        q_a = {}
        for question in self.questions.all():
            answers = question.answer_set.filter(answerpaper=self).distinct()
            if not answers.exists():
                q_a[question] = [None, 0.0]
                continue
            ans_errs = []
            for answer in answers:
                ans_errs.append({
                    'answer': answer,
                    'error_list': [e for e in json.loads(answer.error)]
                })
            q_a[question] = ans_errs
            q_a[question].append(self._get_marks_for_question(question))
        return q_a

    def get_latest_answer(self, question_id):
        return self.answers.filter(question=question_id).order_by("id").last()

    def get_questions(self):
        return self.questions.filter(active=True)

    def get_questions_answered(self):
        return self.questions_answered.all().distinct()

    def get_questions_unanswered(self):
        return self.questions_unanswered.all()

    def is_answer_correct(self, question_id):
        ''' Return marks of a question answered'''
        return self.answers.filter(question_id=question_id,
                                   correct=True).exists()

    def is_attempt_inprogress(self):
        if self.status == 'inprogress':
            return self.time_left() > 0

    def get_previous_answers(self, question):
        return self.answers.filter(question=question).order_by('-id')

    def get_categorized_question_indices(self):
        category_question_map = defaultdict(list)
        for index, question in enumerate(self.get_all_ordered_questions(), 1):
            question_category = legend_display_types.get(question.type)
            if question_category:
                category_question_map[
                    question_category["label"]
                ].append(index)
        return dict(category_question_map)

    def validate_answer(self, user_answer, question, json_data=None, uid=None,
                        server_port=SERVER_POOL_PORT):
        """
            Checks whether the answer submitted by the user is right or wrong.
            If right then returns correct = True, success and
            message = Correct answer.
            success is True for MCQ's and multiple correct choices because
            only one attempt are allowed for them.
            For code questions success is True only if the answer is correct.
        """

        result = {'success': False, 'error': ['Incorrect answer'],
                  'weight': 0.0}
        if user_answer is not None:
            if question.type == 'mcq':
                expected_answer = question.get_test_case(correct=True).id
                if user_answer.strip() == str(expected_answer).strip():
                    result['success'] = True
                    result['error'] = ['Correct answer']

            elif question.type == 'mcc':
                expected_answers = []
                for opt in question.get_test_cases(correct=True):
                    expected_answers.append(str(opt.id))
                if set(user_answer) == set(expected_answers):
                    result['success'] = True
                    result['error'] = ['Correct answer']

            elif question.type == 'integer':
                expected_answers = []
                for tc in question.get_test_cases():
                    expected_answers.append(int(tc.correct))
                if int(user_answer) in expected_answers:
                    result['success'] = True
                    result['error'] = ['Correct answer']

            elif question.type == 'string':
                tc_status = []
                for tc in question.get_test_cases():
                    if tc.string_check == "lower":
                        if tc.correct.lower().splitlines()\
                           == user_answer.lower().splitlines():
                            tc_status.append(True)
                    else:
                        if tc.correct.splitlines()\
                           == user_answer.splitlines():
                            tc_status.append(True)
                if any(tc_status):
                    result['success'] = True
                    result['error'] = ['Correct answer']

            elif question.type == 'float':
                user_answer = float(user_answer)
                tc_status = []
                user_answer = float(user_answer)
                for tc in question.get_test_cases():
                    if abs(tc.correct - user_answer) <= tc.error_margin:
                        tc_status.append(True)
                if any(tc_status):
                    result['success'] = True
                    result['error'] = ['Correct answer']

            elif question.type == 'arrange':
                testcase_ids = sorted(
                                  [tc.id for tc in question.get_test_cases()]
                                  )
                if user_answer == testcase_ids:
                    result['success'] = True
                    result['error'] = ['Correct answer']

            elif question.type == 'code' or question.type == "upload":
                user_dir = self.user.profile.get_user_dir()
                url = '{0}:{1}'.format(SERVER_HOST_NAME, server_port)
                submit(url, uid, json_data, user_dir)
                result = {'uid': uid, 'status': 'running'}
        return result

    def regrade(self, question_id, server_port=SERVER_POOL_PORT):
        try:
            question = self.questions.get(id=question_id)
            msg = 'User: {0}; Quiz: {1}; Question: {2}.\n'.format(
                    self.user, self.question_paper.quiz.description, question)
        except Question.DoesNotExist:
            msg = 'User: {0}; Quiz: {1} Question id: {2}.\n'.format(
                self.user, self.question_paper.quiz.description,
                question_id
            )
            return False, f'{msg} Question not in the answer paper.'
        user_answer = self.answers.filter(question=question).last()
        if not user_answer or not user_answer.answer:
            return False, f'{msg} Did not answer.'
        if question.type in ['mcc', 'arrange']:
            try:
                answer = literal_eval(user_answer.answer)
                if type(answer) is not list:
                    return (False, f'{msg} {question.type} answer not a list.')
            except Exception:
                return (False, f'{msg} {question.type} answer submission error')
        else:
            answer = user_answer.answer
        json_data = question.consolidate_answer_data(answer, self.user, True) \
            if question.type == 'code' else None
        result = self.validate_answer(answer, question,
                                      json_data, user_answer.id,
                                      server_port=server_port
                                      )
        if question.type == "code":
            url = '{0}:{1}'.format(SERVER_HOST_NAME, server_port)
            check_result = get_result_from_code_server(url, result['uid'],
                                                       block=True
                                                       )
            result = json.loads(check_result.get('result'))
        user_answer.correct = result.get('success')
        user_answer.error = json.dumps(result.get('error'))
        if result.get('success'):
            if question.partial_grading and question.type == 'code':
                max_weight = question.get_maximum_test_case_weight()
                factor = result['weight']/max_weight
                user_answer.marks = question.points * factor
            else:
                user_answer.marks = question.points
        else:
            if question.partial_grading and question.type == 'code':
                max_weight = question.get_maximum_test_case_weight()
                factor = result['weight']/max_weight
                user_answer.marks = question.points * factor
            else:
                user_answer.marks = 0
        user_answer.save()
        self.update_marks('completed')
        return True, msg

    def __str__(self):
        u = self.user
        q = self.question_paper.quiz
        return u'AnswerPaper paper of {0} {1} for quiz {2}'\
               .format(u.first_name, u.last_name, q.description)


##############################################################################
class AssignmentUploadManager(models.Manager):

    def get_assignments(self, qp, que_id=None, user_id=None, course_id=None):
        if que_id and user_id:
            assignment_files = AssignmentUpload.objects.filter(
                        assignmentQuestion_id=que_id,
                        answer_paper__user_id=user_id,
                        answer_paper__question_paper=qp,
                        answer_paper__course_id=course_id
                        )
            user_name = assignment_files.values_list(
                "answer_paper__user__first_name",
                "answer_paper__user__last_name"
            )[0]
            file_name = "_".join(user_name)
        else:
            assignment_files = AssignmentUpload.objects.filter(
                        answer_paper__question_paper=qp,
                        answer_paper__course_id=course_id
                        )
            file_name = "{0}_Assignment_files".format(
                            assignment_files[0].answer_paper.course.name
                            )

        return assignment_files, file_name


##############################################################################
class AssignmentUpload(models.Model):
    assignmentQuestion = models.ForeignKey(Question, on_delete=models.CASCADE)
    assignmentFile = models.FileField(upload_to=get_assignment_dir,
                                      max_length=255)
    answer_paper = models.ForeignKey(AnswerPaper, blank=True, null=True,
                                     on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now=True)

    objects = AssignmentUploadManager()

    def __str__(self):
        return f'Assignment File of the user {self.answer_paper.user}'

pre_delete.connect(file_cleanup, sender=AssignmentUpload)


##############################################################################
class TestCase(models.Model):
    question = models.ForeignKey(Question, blank=True, null=True,
                                 on_delete=models.CASCADE)
    type = models.CharField(max_length=24, choices=test_case_types, null=True)


class StandardTestCase(TestCase):
    test_case = models.TextField()
    weight = models.FloatField(default=1.0)
    test_case_args = models.TextField(blank=True)
    hidden = models.BooleanField(default=False)

    def get_field_value(self):
        return {"test_case_type": "standardtestcase",
                "test_case": self.test_case,
                "weight": self.weight,
                "hidden": self.hidden,
                "test_case_args": self.test_case_args}

    def __str__(self):
        return u'Standard TestCase | Test Case: {0}'.format(self.test_case)


class StdIOBasedTestCase(TestCase):
    expected_input = models.TextField(default=None, blank=True, null=True)
    expected_output = models.TextField(default=None)
    weight = models.IntegerField(default=1.0)
    hidden = models.BooleanField(default=False)

    def get_field_value(self):
        return {"test_case_type": "stdiobasedtestcase",
                "expected_output": self.expected_output,
                "expected_input": self.expected_input,
                "hidden": self.hidden,
                "weight": self.weight}

    def __str__(self):
        return u'StdIO Based Testcase | Exp. Output: {0} | Exp. Input: {1}'.\
            format(
                self.expected_output, self.expected_input
            )


class McqTestCase(TestCase):
    options = models.TextField(default=None)
    correct = models.BooleanField(default=False)

    def get_field_value(self):
        return {"test_case_type": "mcqtestcase",
                "options": self.options, "correct": self.correct}

    def __str__(self):
        return u'MCQ Testcase | Correct: {0}'.format(self.correct)


class HookTestCase(TestCase):
    hook_code = models.TextField(default=dedent(
        """\
        def check_answer(user_answer):
           ''' Evaluates user answer to return -
           success - Boolean, indicating if code was executed correctly
           mark_fraction - Float, indicating fraction of the
                          weight to a test case
           error - String, error message if success is false

           In case of assignment upload there will be no user answer '''

           success = False
           err = "Incorrect Answer" # Please make this more specific
           mark_fraction = 0.0

           # write your code here

           return success, err, mark_fraction

        """)

    )
    weight = models.FloatField(default=1.0)
    hidden = models.BooleanField(default=False)

    def get_field_value(self):
        return {"test_case_type": "hooktestcase", "hook_code": self.hook_code,
                "hidden": self.hidden, "weight": self.weight}

    def __str__(self):
        return u'Hook Testcase | Correct: {0}'.format(self.hook_code)


class IntegerTestCase(TestCase):
    correct = models.IntegerField(default=None)

    def get_field_value(self):
        return {"test_case_type": "integertestcase", "correct": self.correct}

    def __str__(self):
        return u'Integer Testcase | Correct: {0}'.format(self.correct)


class StringTestCase(TestCase):
    correct = models.TextField(default=None)
    string_check = models.CharField(max_length=200, choices=string_check_type)

    def get_field_value(self):
        return {"test_case_type": "stringtestcase", "correct": self.correct,
                "string_check": self.string_check}

    def __str__(self):
        return u'String Testcase | Correct: {0}'.format(self.correct)


class FloatTestCase(TestCase):
    correct = models.FloatField(default=None)
    error_margin = models.FloatField(default=0.0, null=True, blank=True,
                                     help_text="Margin of error")

    def get_field_value(self):
        return {"test_case_type": "floattestcase", "correct": self.correct,
                "error_margin": self.error_margin}

    def __str__(self):
        return u'Testcase | Correct: {0} | Error Margin: +or- {1}'.format(
                self.correct, self.error_margin
                )


class ArrangeTestCase(TestCase):
    options = models.TextField(default=None)

    def get_field_value(self):
        return {"test_case_type": "arrangetestcase",
                "options": self.options}

    def __str__(self):
        return u'Arrange Testcase | Option: {0}'.format(self.options)


##############################################################################
class TestCaseOrder(models.Model):
    """Testcase order contains a set of ordered test cases for a given question
        for each user.
    """

    # Answerpaper of the user.
    answer_paper = models.ForeignKey(AnswerPaper, related_name="answer_paper",
                                     on_delete=models.CASCADE)

    # Question in an answerpaper.
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # Order of the test case for a question.
    order = models.TextField()


##############################################################################
class ForumBase(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to=get_image_dir, blank=True,
                              null=True, validators=[validate_image])
    active = models.BooleanField(default=True)
    anonymous = models.BooleanField(default=False)


class Post(ForumBase):
    title = models.CharField(max_length=200)
    target_ct = models.ForeignKey(ContentType,
                                  blank=True,
                                  null=True,
                                  related_name='target_obj',
                                  on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(null=True,
                                            blank=True,
                                            db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')

    def __str__(self):
        return self.title

    def get_last_comment(self):
        return self.comment.last()

    def get_comments_count(self):
        return self.comment.filter(active=True).count()


class Comment(ForumBase):
    post_field = models.ForeignKey(Post, on_delete=models.CASCADE,
                                   related_name='comment')

    def __str__(self):
        return 'Comment by {0}: {1}'.format(self.creator.username,
                                            self.post_field.title)


class TOCManager(models.Manager):

    def get_data(self, course_id, lesson_id):
        contents = TableOfContents.objects.filter(
            course_id=course_id, lesson_id=lesson_id, content__in=[2, 3, 4]
        )
        data = {}
        for toc in contents:
            data[toc] = LessonQuizAnswer.objects.filter(
                toc_id=toc.id).values_list(
                "student_id", flat=True).distinct().count()
        return data

    def get_all_tocs_as_yaml(self, course_id, lesson_id, file_path):
        all_tocs = TableOfContents.objects.filter(
            course_id=course_id, lesson_id=lesson_id,
        )
        if not all_tocs.exists():
            return None
        for toc in all_tocs:
            toc.get_toc_as_yaml(file_path)
        return file_path

    def get_question_stats(self, toc_id):
        answers = LessonQuizAnswer.objects.get_queryset().filter(
            toc_id=toc_id).order_by('id')
        question = TableOfContents.objects.get(id=toc_id).content_object
        if answers.exists():
            answers = answers.values(
                "student__first_name", "student__last_name", "student__email",
                "student_id", "student__profile__roll_number", "toc_id"
                )
            df = pd.DataFrame(answers)
            answers = df.drop_duplicates().to_dict(orient='records')
        return question, answers

    def get_per_tc_ans(self, toc_id, question_type, is_percent=True):
        answers = LessonQuizAnswer.objects.filter(toc_id=toc_id).values(
            "student_id", "answer__answer"
        ).order_by("id")
        data = None
        if answers.exists():
            df = pd.DataFrame(answers)
            grp = df.groupby(["student_id"]).tail(1)
            total_count = grp.count().answer__answer
            data = grp.groupby(["answer__answer"]).count().to_dict().get(
                "student_id")
            if question_type == "mcc":
                tc_ids = []
                mydata = {}
                for i in data.keys():
                    tc_ids.extend(literal_eval(i))
                for j in tc_ids:
                    if j not in mydata:
                        mydata[j] = 1
                    else:
                        mydata[j] += 1
                data = mydata.copy()
            if is_percent:
                for key, value in data.items():
                    data[key] = (value/total_count)*100
        return data, total_count

    def get_answer(self, toc_id, user_id):
        submission = LessonQuizAnswer.objects.filter(
            toc_id=toc_id, student_id=user_id).last()
        question = submission.toc.content_object
        attempted_answer = submission.answer
        if question.type == "mcq":
            submitted_answer = literal_eval(attempted_answer.answer)
            answers = [
                tc.options
                for tc in question.get_test_cases(id=submitted_answer)
            ]
            answer = ",".join(answers)
        elif question.type == "mcc":
            submitted_answer = literal_eval(attempted_answer.answer)
            answers = [
                tc.options
                for tc in question.get_test_cases(id__in=submitted_answer)
            ]
            answer = ",".join(answers)
        else:
            answer = attempted_answer.answer
        return answer, attempted_answer.correct

    def add_contents(self, course_id, lesson_id, user, contents):
        toc = []
        messages = []
        for content in contents:
            name = content.get('name') or content.get('summary')
            if "content_type" not in content or "time" not in content:
                messages.append(
                    (False,
                     f"content_type or time key is missing in {name}")
                )
            else:
                content_type = content.pop('content_type')
                time = content.pop('time')
                if not is_valid_time_format(time):
                    messages.append(
                        (False,
                         f"Invalid time format in {name}. "
                         "Format should be 00:00:00")
                        )
                else:
                    if content_type == 1:
                        topic = Topic.objects.create(**content)
                        toc.append(TableOfContents(
                            course_id=course_id,
                            lesson_id=lesson_id, time=time,
                            content_object=topic, content=content_type
                        ))
                        messages.append(
                            (True, f"{topic.name} added successfully")
                        )
                    else:
                        content['user'] = user
                        test_cases = content.pop("testcase")
                        que_type = content.get('type')
                        if "files" in content:
                            content.pop("files")
                        if "tags" in content:
                            content.pop("tags")
                        if (que_type in ['code', 'upload']):
                            messages.append(
                                (False, f"{que_type} question is not allowed. "
                                 f"{content.get('summary')} is not added")
                            )
                        else:
                            que = Question.objects.create(**content)
                            for test_case in test_cases:
                                test_case_type = test_case.pop(
                                    'test_case_type'
                                )
                                model_class = get_model_class(test_case_type)
                                model_class.objects.get_or_create(
                                    question=que,
                                    **test_case, type=test_case_type
                                )
                            toc.append(TableOfContents(
                                course_id=course_id, lesson_id=lesson_id,
                                time=time, content_object=que,
                                content=content_type
                            ))
                        messages.append(
                            (True, f"{que.summary} added successfully")
                        )
        if toc:
            TableOfContents.objects.bulk_create(toc)
        return messages


class TableOfContents(models.Model):
    toc_types = (
        (1, "Topic"),
        (2, "Graded Quiz"),
        (3, "Exercise"),
        (4, "Poll")
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name='course')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                               related_name='contents')
    time = models.CharField(max_length=100, default=0)
    content = models.IntegerField(choices=toc_types)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    objects = TOCManager()

    class Meta:
        verbose_name_plural = "Table Of Contents"

    def get_toc_text(self):
        if self.content == 1:
            content_name = self.content_object.name
        else:
            content_name = self.content_object.summary
        return content_name

    def get_toc_as_yaml(self, file_path):
        data = {'content_type': self.content, 'time': self.time}
        if self.topics.exists():
            content = self.topics.first()
            data.update(
                {
                    'name': content.name,
                    'description': content.description,
                }
            )
        elif self.questions.exists():
            content = self.questions.first()
            tc_data = []
            for tc in content.get_test_cases():
                _tc_as_dict = model_to_dict(
                    tc, exclude=['id', 'testcase_ptr', 'question'],
                )
                tc_data.append(_tc_as_dict)
            data.update(
                {
                    'summary': content.summary,
                    'type': content.type,
                    'language': content.language,
                    'description': content.description,
                    'points': content.points,
                    'testcase': tc_data,
                }
            )
        yaml_block = dict_to_yaml(data)
        with open(file_path, "a") as yaml_file:
            yaml_file.write(yaml_block)
            return yaml_file

    def __str__(self):
        return f"TOC for {self.lesson.name} with {self.get_content_display()}"


class Topic(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    content = GenericRelation(TableOfContents, related_query_name='topics')

    def __str__(self):
        return f"{self.name}"


class LessonQuizAnswer(models.Model):
    toc = models.ForeignKey(TableOfContents, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    def check_answer(self, user_answer):
        result = {'success': False, 'error': ['Incorrect answer'],
                  'weight': 0.0}
        question = self.toc.content_object
        if question.type == 'mcq':
            expected_answer = question.get_test_case(correct=True).id
            if user_answer.strip() == str(expected_answer).strip():
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'mcc':
            expected_answers = [
                str(opt.id) for opt in question.get_test_cases(correct=True)
            ]
            if set(user_answer) == set(expected_answers):
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'integer':
            expected_answers = [
                int(tc.correct) for tc in question.get_test_cases()
            ]
            if int(user_answer) in expected_answers:
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'string':
            tc_status = []
            for tc in question.get_test_cases():
                if tc.string_check == "lower":
                    if tc.correct.lower().splitlines()\
                       == user_answer.lower().splitlines():
                        tc_status.append(True)
                else:
                    if tc.correct.splitlines()\
                       == user_answer.splitlines():
                        tc_status.append(True)
            if any(tc_status):
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'float':
            user_answer = float(user_answer)
            tc_status = []
            for tc in question.get_test_cases():
                if abs(tc.correct - user_answer) <= tc.error_margin:
                    tc_status.append(True)
            if any(tc_status):
                result['success'] = True
                result['error'] = ['Correct answer']

        elif question.type == 'arrange':
            testcase_ids = sorted(
                              [tc.id for tc in question.get_test_cases()]
                              )
            if user_answer == testcase_ids:
                result['success'] = True
                result['error'] = ['Correct answer']
        self.answer.error = result
        ans_status = result.get("success")
        self.answer.correct = ans_status
        if ans_status:
            self.answer.marks = self.answer.question.points
        self.answer.save()
        return result

    def __str__(self):
        return f"Lesson answer of {self.toc} by {self.student.get_full_name()}"


class MicroManager(models.Model):
    manager = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='micromanaging', null=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='micromanaged')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True)
    special_attempt = models.BooleanField(default=False)
    attempts_permitted = models.IntegerField(default=0)
    permitted_time = models.DateTimeField(default=timezone.now)
    attempts_utilised = models.IntegerField(default=0)
    wait_time = models.IntegerField('Days to wait before special attempt',
                                    default=0)
    attempt_valid_for = models.IntegerField('Validity days', default=90)

    class Meta:
        unique_together = ('student', 'course', 'quiz')

    def set_wait_time(self, days=0):
        self.wait_time = days
        self.save()

    def increment_attempts_permitted(self):
        self.attempts_permitted += 1
        self.save()

    def update_permitted_time(self, permit_time=None):
        time_now = timezone.now()
        self.permitted_time = time_now if not permit_time else permit_time
        self.save()

    def has_student_attempts_exhausted(self):
        if self.quiz.attempts_allowed == -1:
            return False
        question_paper = self.quiz.questionpaper_set.first()
        attempts = AnswerPaper.objects.get_total_attempt(
            question_paper, self.student, course_id=self.course.id
        )
        last_attempt = AnswerPaper.objects.get_user_last_attempt(
            question_paper, self.student, self.course.id
        )
        if last_attempt:
            if last_attempt.is_attempt_inprogress():
                return False
        return attempts >= self.quiz.attempts_allowed

    def is_last_attempt_inprogress(self):
        question_paper = self.quiz.questionpaper_set.first()
        last_attempt = AnswerPaper.objects.get_user_last_attempt(
            question_paper, self.student, self.course.id
        )
        if last_attempt:
            return last_attempt.is_attempt_inprogress()
        return False

    def has_quiz_time_exhausted(self):
        return not self.quiz.active or self.quiz.is_expired()

    def is_course_exhausted(self):
        return not self.course.active or not self.course.is_active_enrollment()

    def is_special_attempt_required(self):
        return (self.has_student_attempts_exhausted() or
                self.has_quiz_time_exhausted() or self.is_course_exhausted())

    def allow_special_attempt(self, wait_time=0):
        if (self.is_special_attempt_required() and
                not self.is_last_attempt_inprogress()):
            self.special_attempt = True
            if self.attempts_utilised >= self.attempts_permitted:
                self.increment_attempts_permitted()
            self.update_permitted_time()
            self.set_wait_time(days=wait_time)
            self.save()

    def has_special_attempt(self):
        return (self.special_attempt and
                (self.attempts_utilised < self.attempts_permitted))

    def is_attempt_time_valid(self):
        permit_time = self.permitted_time
        wait_time = permit_time + timezone.timedelta(days=self.wait_time)
        valid_time = permit_time + timezone.timedelta(
            days=self.attempt_valid_for)
        return wait_time <= timezone.now() <= valid_time

    def can_student_attempt(self):
        return self.has_special_attempt() and self.is_attempt_time_valid()

    def get_attempt_number(self):
        return self.quiz.attempts_allowed + self.attempts_utilised + 1

    def increment_attempts_utilised(self):
        self.attempts_utilised += 1
        self.save()

    def revoke_special_attempt(self):
        self.special_attempt = False
        self.save()

    def __str__(self):
        return 'MicroManager for {0} - {1}'.format(self.student.username,
                                                   self.course.name)


class QRcode(models.Model):
    random_key = models.CharField(max_length=128, blank=True)
    short_key = models.CharField(max_length=128, null=True, unique=True)
    image = models.ImageField(upload_to='qrcode', blank=True)
    used = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    handler = models.ForeignKey('QRcodeHandler', on_delete=models.CASCADE)

    def __str__(self):
        return 'QRcode {0}'.format(self.short_key)

    def is_active(self):
        return self.active

    def is_used(self):
        return self.used

    def deactivate(self):
        self.active = False

    def activate(self):
        self.active = True

    def set_used(self):
        self.used = True

    def set_random_key(self):
        key = hashlib.sha1('{0}'.format(self.id).encode()).hexdigest()
        self.random_key = key

    def set_short_key(self):
        key = self.random_key
        if key:
            num = 5
            for i in range(40):
                try:
                    self.short_key = key[0:num]
                    self.save()
                    break
                except IntegrityError:
                    num = num + 1

    def is_qrcode_available(self):
        return self.active and not self.used and self.image is not None

    def generate_image(self, content):
        img = qrcode.make(content)
        qr_dir = os.path.join(settings.MEDIA_ROOT, 'qrcode')
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir)
        path = os.path.join(qr_dir, f'{self.short_key}.png')
        img.save(path)
        with open(path, "rb") as qr_file:
            django_file = File(qr_file)
            self.activate()
            self.image.save(os.path.basename(path), django_file, save=True)


class QRcodeHandler(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answerpaper = models.ForeignKey(AnswerPaper, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self):
        return 'QRcode Handler for  {0}'.format(self.user.username)

    def get_qrcode(self):
        qrcodes = self.qrcode_set.filter(active=True, used=False)
        if qrcodes.exists():
            return qrcodes.last()
        else:
            return self._create_qrcode()

    def _create_qrcode(self):
        qrcode = QRcode.objects.create(handler=self)
        qrcode.set_random_key()
        qrcode.set_short_key()
        return qrcode

    def can_use(self):
        return self.answerpaper.is_attempt_inprogress()
