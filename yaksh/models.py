from __future__ import unicode_literals, division
from datetime import datetime, timedelta
import json
import random
import ruamel.yaml
from ruamel.yaml.scalarstring import PreservedScalarString
from ruamel.yaml.comments import CommentedMap
from random import sample
from collections import Counter, defaultdict

from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from taggit.managers import TaggableManager
from django.utils import timezone
from django.core.files import File
import glob

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
from .file_utils import extract_files, delete_files
from django.template import Context, Template
from yaksh.code_server import (
    submit, get_result as get_result_from_code_server
)
from yaksh.settings import SERVER_POOL_PORT, SERVER_HOST_NAME
from django.conf import settings
from django.forms.models import model_to_dict
from grades.models import GradingSystem

languages = (
        ("python", "Python"),
        ("bash", "Bash"),
        ("c", "C Language"),
        ("cpp", "C++ Language"),
        ("java", "Java Language"),
        ("scilab", "Scilab"),
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
    folder_name = instance.course.name.replace(" ", "_")
    sub_folder_name = instance.question_paper.quiz.description.replace(
        " ", "_")
    return os.sep.join((folder_name, sub_folder_name, instance.user.username,
                        str(instance.assignmentQuestion.id),
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
        upload_dir = instance.lesson.name.replace(" ", "_")
    else:
        upload_dir = instance.name.replace(" ", "_")
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
    creator = models.ForeignKey(User)

    # Activate/Deactivate Lesson
    active = models.BooleanField(default=True)

    # A video file
    video_file = models.FileField(
        upload_to=get_file_dir, default=None,
        null=True, blank=True,
        help_text="Please upload video files in mp4, ogv, webm format"
        )

    def __str__(self):
        return "{0}".format(self.name)

    def get_files(self):
        return LessonFile.objects.filter(lesson=self)

    def _create_lesson_copy(self, user):
        lesson_files = self.get_files()
        new_lesson = self
        new_lesson.id = None
        new_lesson.name = "Copy of {0}".format(self.name)
        new_lesson.creator = user
        new_lesson.save()
        for _file in lesson_files:
            file_name = os.path.basename(_file.file.name)
            if os.path.exists(_file.file.path):
                lesson_file = open(_file.file.path, "rb")
                django_file = File(lesson_file)
                lesson_file_obj = LessonFile()
                lesson_file_obj.lesson = new_lesson
                lesson_file_obj.file.save(file_name, django_file, save=True)
        return new_lesson

    def remove_file(self):
        if self.video_file:
            file_path = self.video_file.path
            if os.path.exists(file_path):
                os.remove(file_path)

    def _add_lesson_to_zip(self, module, course, zip_file, path):
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
            path, "templates", "yaksh", "unit.html"
            ))
        lesson_data = {"course": course, "module": module,
                       "lesson": self, "lesson_files": lesson_files}
        write_templates_to_zip(zip_file, unit_file_path, lesson_data,
                               lesson_name, sub_folder_name)


#############################################################################
class LessonFile(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="lesson")
    file = models.FileField(upload_to=get_file_dir, default=None)

    def remove(self):
        if os.path.exists(self.file.path):
            os.remove(self.file.path)
            if os.listdir(os.path.dirname(self.file.path)) == []:
                os.rmdir(os.path.dirname(self.file.path))
        self.delete()


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

    creator = models.ForeignKey(User, null=True)

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
            user=user, course=course, question_paper=qp
        ).order_by("-attempt_number")
        if ans_ppr.exists():
            status = ans_ppr.first().status
        else:
            status = "not attempted"
        return status

    def _create_quiz_copy(self, user):
        question_papers = self.questionpaper_set.all()
        new_quiz = self
        new_quiz.id = None
        new_quiz.description = "Copy of {0}".format(self.description)
        new_quiz.creator = user
        new_quiz.save()
        for qp in question_papers:
            qp._create_duplicate_questionpaper(new_quiz)
        return new_quiz

    def __str__(self):
        desc = self.description or 'Quiz'
        return '%s: on %s for %d minutes' % (desc, self.start_date_time,
                                             self.duration)


##########################################################################
class LearningUnit(models.Model):
    """ Maintain order of lesson and quiz added in the course """
    order = models.IntegerField()
    type = models.CharField(max_length=16)
    lesson = models.ForeignKey(Lesson, null=True, blank=True)
    quiz = models.ForeignKey(Quiz, null=True, blank=True)
    check_prerequisite = models.BooleanField(default=True)

    def toggle_check_prerequisite(self):
        if self.check_prerequisite:
            self.check_prerequisite = False
        else:
            self.check_prerequisite = True

    def get_completion_status(self, user, course):
        course_status = CourseStatus.objects.filter(user=user, course=course)
        state = "not attempted"
        if course_status.exists():
            if self in course_status.first().completed_units.all():
                state = "completed"
            elif self.type == "quiz":
                state = self.quiz.get_answerpaper_status(user, course)
            elif course_status.first().current_unit == self:
                state = "inprogress"
        return state

    def has_prerequisite(self):
        return self.check_prerequisite

    def is_prerequisite_passed(self, user, learning_module, course):
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


###############################################################################
class LearningModule(models.Model):
    """ Learning Module to maintain learning units"""
    learning_unit = models.ManyToManyField(LearningUnit,
                                           related_name="learning_unit")
    name = models.CharField(max_length=255)
    description = models.TextField(default=None, null=True, blank=True)
    order = models.IntegerField(default=0)
    creator = models.ForeignKey(User, related_name="module_creator")
    check_prerequisite = models.BooleanField(default=True)
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

    def is_prerequisite_passed(self, user, course):
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

    def _create_module_copy(self, user, module_name):
        learning_units = self.learning_unit.order_by("order")
        new_module = self
        new_module.id = None
        new_module.name = module_name
        new_module.creator = user
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
        for lesson in lessons:
            lesson._add_lesson_to_zip(self, course, zip_file, path)
        module_file_path = os.sep.join((
            path, "templates", "yaksh", "module.html"
            ))
        module_data = {"course": course, "module": self, "lessons": lessons}
        write_templates_to_zip(zip_file, module_file_path, module_data,
                               module_name, folder_name)

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
    creator = models.ForeignKey(User, related_name='creator')
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

    grading_system = models.ForeignKey(GradingSystem, null=True, blank=True)

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
            copy_module_name = "Copy of {0}".format(module.name)
            new_module = module._create_module_copy(user, copy_module_name)
            new_course.learning_module.add(new_module)

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
        return user in self.students.all()

    def is_creator(self, user):
        return self.creator == user

    def is_teacher(self, user):
        return True if user in self.teachers.all() else False

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
        teachers = list(self.teachers.all().values_list("id", flat=True))
        teachers.append(self.creator.id)
        students = self.students.exclude(id__in=teachers)
        return students

    def get_learning_modules(self):
        return self.learning_module.order_by("order")

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
        course_status = CourseStatus.objects.filter(course=self, user=user)
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
        return user in self.students.all()

    def create_zip(self, path, static_files):
        zip_file_name = string_io()
        with zipfile.ZipFile(zip_file_name, "a") as zip_file:
            course_name = self.name.replace(" ", "_")
            modules = self.get_learning_modules()
            file_path = os.sep.join((path, "templates", "yaksh", "index.html"))
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
                                     null=True, blank=True)
    course = models.ForeignKey(Course)
    user = models.ForeignKey(User)
    grade = models.CharField(max_length=255, null=True, blank=True)
    percentage = models.FloatField(default=0.0)
    percent_completed = models.IntegerField(default=0)

    def get_grade(self):
        return self.grade

    def set_grade(self):
        if self.is_course_complete():
            self.calculate_percentage()
            if self.course.grading_system is None:
                grading_system = GradingSystem.objects.get(name='default')
            else:
                grading_system = self.course.grading_system
            grade = grading_system.get_grade(self.percentage)
            self.grade = grade
            self.save()

    def calculate_percentage(self):
        if self.is_course_complete():
            quizzes = self.course.get_quizzes()
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


###############################################################################
class ConcurrentUser(models.Model):
    concurrent_user = models.OneToOneField(User)
    session_key = models.CharField(max_length=40)


###############################################################################
class Profile(models.Model):
    """Profile for a user to store roll number and other details."""
    user = models.OneToOneField(User)
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

        user_dir = join(settings.OUTPUT_DIR, str(self.user.username))
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
        return '%s' % (self.user.get_full_name())


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
    user = models.ForeignKey(User, related_name="user")

    # Does this question allow partial grading
    partial_grading = models.BooleanField(default=False)

    # Check assignment upload based question
    grade_assignment_upload = models.BooleanField(default=False)

    min_time = models.IntegerField("time in minutes", default=0)

    # Solution for the question.
    solution = models.TextField(blank=True)

    def consolidate_answer_data(self, user_answer, user=None):
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
            metadata['file_paths'] = [(file.file.path, file.extract)
                                      for file in files]
        if self.type == "upload":
            assignment_files = AssignmentUpload.objects.filter(
                assignmentQuestion=self, user=user
                )
            if assignment_files:
                metadata['assign_files'] = [(file.assignmentFile.path, False)
                                            for file in assignment_files]
        question_data['metadata'] = metadata

        return json.dumps(question_data)

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
            q_dict['tags'] = [tags.tag.name for tags in q_dict['tags']]
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
            zip_file.write(f.file.path, os.path.join("additional_files",
                                                     os.path.basename(
                                                        f.file.path
                                                        )
                                                     )
                           )
            files_list.append(((os.path.basename(f.file.path)), f.extract))
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

    def __str__(self):
        return self.summary


###############################################################################
class FileUpload(models.Model):
    file = models.FileField(upload_to=get_upload_dir, blank=True)
    question = models.ForeignKey(Question, related_name="question")
    extract = models.BooleanField(default=False)
    hide = models.BooleanField(default=False)

    def remove(self):
        if os.path.exists(self.file.path):
            os.remove(self.file.path)
            if os.listdir(os.path.dirname(self.file.path)) == []:
                os.rmdir(os.path.dirname(self.file.path))
        self.delete()

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


###############################################################################
class Answer(models.Model):
    """Answers submitted by the users."""

    # The question for which user answers.
    question = models.ForeignKey(Question)

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

    def set_marks(self, marks):
        if marks > self.question.points:
            self.marks = self.question.points
        else:
            self.marks = marks

    def __str__(self):
        return self.answer


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
            trial_questionpaper = self.get(quiz=trial_quiz)
        else:
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
    quiz = models.ForeignKey(Quiz)

    # Questions that will be mandatory in the quiz.
    fixed_questions = models.ManyToManyField(Question)

    # Questions that will be fetched randomly from the Question Set.
    random_questions = models.ManyToManyField("QuestionSet")

    # Option to shuffle questions, each time a new question paper is created.
    shuffle_questions = models.BooleanField(default=False, blank=False)

    # Total marks for the question paper.
    total_marks = models.FloatField(default=0.0, blank=True)

    # Sequence or Order of fixed questions
    fixed_question_order = models.CharField(max_length=255, blank=True)

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
            marks += question_set.marks * question_set.num_questions
        self.total_marks = marks

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

    def make_answerpaper(self, user, ip, attempt_num, course_id):
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
    def get_all_questions(self, questionpaper_id, attempt_number, course_id,
                          status='completed'):
        ''' Return a dict of question id as key and count as value'''
        papers = self.filter(question_paper_id=questionpaper_id,
                             course_id=course_id,
                             attempt_number=attempt_number, status=status)
        all_questions = list()
        questions = list()
        for paper in papers:
            all_questions += paper.get_questions()
        for question in all_questions:
            questions.append(question.id)
        return Counter(questions)

    def get_all_questions_answered(self, questionpaper_id, attempt_number,
                                   course_id, status='completed'):
        ''' Return a dict of answered question id as key and count as value'''
        papers = self.filter(question_paper_id=questionpaper_id,
                             course_id=course_id,
                             attempt_number=attempt_number, status=status)
        questions_answered = list()
        for paper in papers:
            for question in filter(None, paper.get_questions_answered()):
                if paper.is_answer_correct(question):
                    questions_answered.append(question.id)
        return Counter(questions_answered)

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
            The list contains two value, first the number of times a question
            was answered correctly, and second the number of times a question
            appeared in a quiz'''
        question_stats = {}
        questions_answered = self.get_all_questions_answered(questionpaper_id,
                                                             attempt_number,
                                                             course_id)
        questions = self.get_all_questions(questionpaper_id, attempt_number,
                                           course_id)
        all_questions = Question.objects.filter(
                id__in=set(questions),
                active=True
            ).order_by('type')
        for question in all_questions:
            if question.id in questions_answered:
                question_stats[question] = [questions_answered[question.id],
                                            questions[question.id]]
            else:
                question_stats[question] = [0, questions[question.id]]
        return question_stats

    def _get_answerpapers_for_quiz(self, questionpaper_id, course_id,
                                   status=False):
        if not status:
            return self.filter(question_paper_id=questionpaper_id,
                               course_id=course_id)
        else:
            return self.filter(question_paper_id=questionpaper_id,
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
        return self.filter(question_paper=questionpaper, user=user,
                           course_id=course_id)\
                            .order_by('-attempt_number')

    def get_user_data(self, user, questionpaper_id, course_id,
                      attempt_number=None):
        if attempt_number is not None:
            papers = self.filter(user=user, question_paper_id=questionpaper_id,
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
        papers = self.filter(question_paper__quiz=quiz, course_id=course_id,
                             user=user_id).values("marks_obtained")
        if papers:
            best_attempt = max([marks["marks_obtained"] for marks in papers])
        return best_attempt


###############################################################################
class AnswerPaper(models.Model):
    """A answer paper for a student -- one per student typically.
    """
    # The user taking this question paper.
    user = models.ForeignKey(User)

    questions = models.ManyToManyField(Question, related_name='questions')

    # The Quiz to which this question paper is attached to.
    question_paper = models.ForeignKey(QuestionPaper)

    # Answepaper will be unique to the course
    course = models.ForeignKey(Course, null=True)

    # The attempt number for the question paper.
    attempt_number = models.IntegerField()

    # The time when this paper was started by the user.
    start_time = models.DateTimeField()

    # The time when this paper was ended by the user.
    end_time = models.DateTimeField()

    # User's IP which is logged.
    user_ip = models.CharField(max_length=15)

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
    passed = models.NullBooleanField()

    # Status of the quiz attempt
    status = models.CharField(
        max_length=20, choices=test_status,
        default='inprogress'
    )

    # set question order
    questions_order = models.TextField(blank=True, default='')

    objects = AnswerPaperManager()

    class Meta:
        unique_together = ('user', 'question_paper',
                           'attempt_number', "course"
                           )

    def get_per_question_score(self, question_id):
        questions = self.get_questions().values_list('id', flat=True)
        if question_id not in questions:
            return 'NA'
        answer = self.get_latest_answer(question_id)
        if answer:
            return answer.marks
        else:
            return 0

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

    def time_left(self):
        """Return the time remaining for the user in seconds."""
        secs = self._get_total_seconds()
        total = self.question_paper.quiz.duration*60.0
        remain = max(total - secs, 0)
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

    def _update_marks_obtained(self):
        """Updates the total marks earned by student for this paper."""
        marks = 0
        for question in self.questions.all():
            marks_list = [a.marks
                          for a in self.answers.filter(question=question)]
            max_marks = max(marks_list) if marks_list else 0.0
            marks += max_marks
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

    def get_question_answers(self):
        """
            Return a dictionary with keys as questions and a list of the
            corresponding answers.
        """
        q_a = {}
        for answer in self.answers.all():
            question = answer.question
            if question in q_a:
                q_a[question].append({
                    'answer': answer,
                    'error_list': [e for e in json.loads(answer.error)]
                })
            else:
                q_a[question] = [{
                    'answer': answer,
                    'error_list': [e for e in json.loads(answer.error)]
                }]
        return q_a

    def get_latest_answer(self, question_id):
        return self.answers.filter(question=question_id).order_by("id").last()

    def get_questions(self):
        return self.questions.filter(active=True)

    def get_questions_answered(self):
        return self.questions_answered.all()

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
            return False, msg + 'Question not in the answer paper.'
        user_answer = self.answers.filter(question=question).last()
        if not user_answer:
            return False, msg + 'Did not answer.'
        if question.type in ['mcc', 'arrange']:
            try:
                answer = literal_eval(user_answer.answer)
                if type(answer) is not list:
                    return (False,
                            msg + '{0} answer not a list.'.format(
                                                            question.type
                                                            )
                            )
            except Exception:
                return (False,
                        msg + '{0} answer submission error'.format(
                                                             question.type
                                                             )
                        )
        else:
            answer = user_answer.answer
        json_data = question.consolidate_answer_data(answer) \
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
                        assignmentQuestion_id=que_id, user_id=user_id,
                        question_paper=qp, course_id=course_id
                        )
            file_name = User.objects.get(id=user_id).get_full_name()
        else:
            assignment_files = AssignmentUpload.objects.filter(
                        question_paper=qp, course_id=course_id
                        )
            file_name = "{0}_Assignment_files".format(
                            assignment_files[0].course.name
                            )

        return assignment_files, file_name


##############################################################################
class AssignmentUpload(models.Model):
    user = models.ForeignKey(User)
    assignmentQuestion = models.ForeignKey(Question)
    assignmentFile = models.FileField(upload_to=get_assignment_dir)
    question_paper = models.ForeignKey(QuestionPaper, blank=True, null=True)
    course = models.ForeignKey(Course, null=True, blank=True)
    objects = AssignmentUploadManager()


##############################################################################
class TestCase(models.Model):
    question = models.ForeignKey(Question, blank=True, null=True)
    type = models.CharField(max_length=24, choices=test_case_types, null=True)


class StandardTestCase(TestCase):
    test_case = models.TextField()
    weight = models.FloatField(default=1.0)
    test_case_args = models.TextField(blank=True)

    def get_field_value(self):
        return {"test_case_type": "standardtestcase",
                "test_case": self.test_case,
                "weight": self.weight,
                "test_case_args": self.test_case_args}

    def __str__(self):
        return u'Standard TestCase | Test Case: {0}'.format(self.test_case)


class StdIOBasedTestCase(TestCase):
    expected_input = models.TextField(default=None, blank=True, null=True)
    expected_output = models.TextField(default=None)
    weight = models.IntegerField(default=1.0)

    def get_field_value(self):
        return {"test_case_type": "stdiobasedtestcase",
                "expected_output": self.expected_output,
                "expected_input": self.expected_input,
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

    def get_field_value(self):
        return {"test_case_type": "hooktestcase", "hook_code": self.hook_code,
                "weight": self.weight}

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
    answer_paper = models.ForeignKey(AnswerPaper, related_name="answer_paper")

    # Question in an answerpaper.
    question = models.ForeignKey(Question)

    # Order of the test case for a question.
    order = models.TextField()

##############################################################################
