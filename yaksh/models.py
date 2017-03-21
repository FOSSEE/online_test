from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
from random import sample
from collections import Counter
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from taggit.managers import TaggableManager
from django.utils import timezone
from django.core.files import File
try:
    from StringIO import StringIO as string_io
except ImportError:
    from io import BytesIO as string_io
import pytz
import os
import sys
import traceback
import stat
from os.path import join, exists
import shutil
import zipfile
import tempfile
from textwrap import dedent
from .file_utils import extract_files, delete_files
from yaksh.xmlrpc_clients import code_server
from django.conf import settings


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
    )

enrollment_methods = (
    ("default", "Enroll Request"),
    ("open", "Open Course"),
    )

test_case_types = (
        ("standardtestcase", "Standard Testcase"),
        ("stdiobasedtestcase", "StdIO Based Testcase"),
        ("mcqtestcase", "MCQ Testcase"),
        ("hooktestcase", "Hook Testcase"),
        ("integertestcase", "Integer Testcase"),
        ("stringtestcase", "String Testcase"),
        ("floattestcase", "Float Testcase"),
    )

string_check_type = (
    ("lower", "Case Insensitive"),
    ("exact", "Case Sensitive"),
    )

attempts = [(i, i) for i in range(1, 6)]
attempts.append((-1, 'Infinite'))
days_between_attempts = [(j, j) for j in range(401)]

test_status = (
                ('inprogress', 'Inprogress'),
                ('completed', 'Completed'),
              )


def get_assignment_dir(instance, filename):
    return os.sep.join((
        instance.user.username, str(instance.assignmentQuestion.id), filename
    ))


def get_model_class(model):
    ctype = ContentType.objects.get(app_label="yaksh", model=model)
    model_class = ctype.model_class()

    return model_class


def has_profile(user):
    """ check if user has profile """
    return True if hasattr(user, 'profile') else False


def get_upload_dir(instance, filename):
    return os.sep.join((
        'question_%s' % (instance.question.id), filename
    ))


###############################################################################
class CourseManager(models.Manager):

    def create_trial_course(self, user):
        """Creates a trial course for testing questions"""
        trial_course = self.create(name="trial_course", enrollment="open",
                                   creator=user, is_trial=True)
        trial_course.enroll(False, user)
        return trial_course


###############################################################################
class Course(models.Model):
    """ Course for students"""
    name = models.CharField(max_length=128)
    enrollment = models.CharField(max_length=32, choices=enrollment_methods)
    active = models.BooleanField(default=True)
    creator = models.ForeignKey(User, related_name='creator')
    students = models.ManyToManyField(User, related_name='students')
    requests = models.ManyToManyField(User, related_name='requests')
    rejected = models.ManyToManyField(User, related_name='rejected')
    created_on = models.DateTimeField(auto_now_add=True)
    teachers = models.ManyToManyField(User, related_name='teachers')
    is_trial = models.BooleanField(default=False)
    instructions = models.TextField(default=None, null=True, blank=True)
    objects = CourseManager()

    def request(self, *users):
        self.requests.add(*users)

    def get_requests(self):
        return self.requests.all()

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

    def get_quizzes(self):
        return self.quiz_set.filter(is_trial=False)

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
        course = Course.objects.filter(creator=user, name="Yaksh Demo course")
        if not course:
            course = Course.objects.create(name="Yaksh Demo course",
                                           enrollment="open",
                                           creator=user)
            quiz = Quiz()
            demo_quiz = quiz.create_demo_quiz(course)
            demo_ques = Question()
            demo_ques.create_demo_questions(user)
            demo_que_ppr = QuestionPaper()
            demo_que_ppr.create_demo_quiz_ppr(demo_quiz, user)
            success = True
        else:
            success = False
        return success

    def get_only_students(self):
        teachers = list(self.teachers.all().values_list("id", flat=True))
        teachers.append(self.creator.id)
        students = self.students.exclude(id__in=teachers)
        return students

    def __str__(self):
        return self.name


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
    timezone = models.CharField(
        max_length=64,
        default=pytz.utc.zone,
        choices=[(tz, tz) for tz in pytz.common_timezones]
    )

    def get_user_dir(self):
        """Return the output directory for the user."""

        user_dir = join(settings.OUTPUT_DIR, str(self.user.username))
        if not exists(user_dir):
            os.makedirs(user_dir)
            os.chmod(user_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        return user_dir


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
    snippet = models.CharField(max_length=256, blank=True)

    # user for particular question
    user = models.ForeignKey(User, related_name="user")

    # Does this question allow partial grading
    partial_grading = models.BooleanField(default=False)

    # Check assignment upload based question
    grade_assignment_upload = models.BooleanField(default=False)

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
        questions = Question.objects.filter(
            id__in=question_ids, user_id=user.id, active=True
        )
        questions_dict = []
        zip_file_name = string_io()
        zip_file = zipfile.ZipFile(zip_file_name, "a")
        for question in questions:
            test_case = question.get_test_cases()
            file_names = question._add_and_get_files(zip_file)
            q_dict = {
                'summary': question.summary,
                'description': question.description,
                'points': question.points, 'language': question.language,
                'type': question.type, 'active': question.active,
                'snippet': question.snippet,
                'testcase': [case.get_field_value() for case in test_case],
                'files': file_names
            }
            questions_dict.append(q_dict)
        question._add_json_to_zip(zip_file, questions_dict)
        return zip_file_name

    def load_questions(self, questions_list, user, file_path=None,
                       files_list=None):
        try:
            questions = json.loads(questions_list)
        except ValueError as exc_msg:
            msg = "Error Parsing Json: {0}".format(exc_msg)
            return msg
        for question in questions:
            question['user'] = user
            file_names = question.pop('files')
            test_cases = question.pop('testcase')
            que, result = Question.objects.get_or_create(**question)
            if file_names:
                que._add_files_to_db(file_names, file_path)
            for test_case in test_cases:
                test_case_type = test_case.pop('test_case_type')
                model_class = get_model_class(test_case_type)
                new_test_case, obj_create_status = \
                    model_class.objects.get_or_create(
                        question=que, **test_case
                    )
                new_test_case.type = test_case_type
                new_test_case.save()
        return "Questions Uploaded Successfully"

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

    def get_maximum_test_case_weight(self, **kwargs):
        max_weight = 0.0
        for test_case in self.get_test_cases():
            max_weight += test_case.weight

        return max_weight

    def _add_and_get_files(self, zip_file):
        files = FileUpload.objects.filter(question=self)
        files_list = []
        for f in files:
            zip_file.write(f.file.path, (os.path.basename(f.file.path)))
            files_list.append(((os.path.basename(f.file.path)), f.extract))
        return files_list

    def _add_files_to_db(self, file_names, path):
        for file_name, extract in file_names:
            q_file = os.path.join(path, file_name)
            if os.path.exists(q_file):
                que_file = open(q_file, 'rb')
                # Converting to Python file object with
                # some Django-specific additions
                django_file = File(que_file)
                file_upload = FileUpload()
                file_upload.question = self
                file_upload.extract = extract
                file_upload.file.save(file_name, django_file, save=True)

    def _add_json_to_zip(self, zip_file, q_dict):
        json_data = json.dumps(q_dict, indent=2)
        tmp_file_path = tempfile.mkdtemp()
        json_path = os.path.join(tmp_file_path, "questions_dump.json")
        with open(json_path, "w") as json_file:
            json_file.write(json_data)
        zip_file.write(json_path, os.path.basename(json_path))
        zip_file.close()
        shutil.rmtree(tmp_file_path)

    def read_json(self, file_path, user, files=None):
        json_file = os.path.join(file_path, "questions_dump.json")
        msg = ""
        if os.path.exists(json_file):
            with open(json_file, 'r') as q_file:
                questions_list = q_file.read()
                msg = self.load_questions(questions_list, user, file_path, files)
        else:
            msg = "Please upload zip file with questions_dump.json in it."

        if files:
            delete_files(files, file_path)
        return msg

    def create_demo_questions(self, user):
        zip_file_path = os.path.join(
            settings.FIXTURE_DIRS, 'demo_questions.zip'
        )
        files, extract_path = extract_files(zip_file_path)
        self.read_json(extract_path, user, files)

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
class QuizManager(models.Manager):
    def get_active_quizzes(self):
        return self.filter(active=True, is_trial=False)

    def create_trial_quiz(self, trial_course, user):
        """Creates a trial quiz for testing questions"""
        trial_quiz = self.create(course=trial_course,
                                 duration=1000,
                                 description="trial_questions",
                                 is_trial=True,
                                 time_between_attempts=0
                                 )
        return trial_quiz

    def create_trial_from_quiz(self, original_quiz_id, user, godmode):
        """Creates a trial quiz from existing quiz"""
        trial_quiz_name = "Trial_orig_id_{0}_{1}".format(
            original_quiz_id,
            "godmode" if godmode else "usermode"
        )

        if self.filter(description=trial_quiz_name).exists():
            trial_quiz = self.get(description=trial_quiz_name)

        else:
            trial_quiz = self.get(id=original_quiz_id)
            trial_quiz.course.enroll(False, user)
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
        return trial_quiz


###############################################################################
class Quiz(models.Model):
    """A quiz that students will participate in. One can think of this
    as the "examination" event.
    """

    course = models.ForeignKey(Course)

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

    # List of prerequisite quizzes to be passed to take this quiz
    prerequisite = models.ForeignKey("Quiz", null=True, blank=True)

    # Programming language for a quiz
    language = models.CharField(max_length=20, choices=languages)

    # Number of attempts for the quiz
    attempts_allowed = models.IntegerField(default=1, choices=attempts)

    time_between_attempts = models.IntegerField(
        "Number of Days", choices=days_between_attempts
    )

    is_trial = models.BooleanField(default=False)

    instructions = models.TextField('Instructions for Students',
                                    default=None, blank=True, null=True)

    view_answerpaper = models.BooleanField('Allow student to view their answer\
                                            paper', default=False)

    allow_skip = models.BooleanField("Allow students to skip questions",
                                     default=True)

    objects = QuizManager()

    class Meta:
        verbose_name_plural = "Quizzes"

    def is_expired(self):
        return not self.start_date_time <= timezone.now() < self.end_date_time

    def has_prerequisite(self):
        return True if self.prerequisite else False

    def create_demo_quiz(self, course):
        demo_quiz = Quiz.objects.create(
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(176590),
            duration=30, active=True,
            attempts_allowed=-1,
            time_between_attempts=0,
            description='Yaksh Demo quiz', pass_criteria=0,
            language='Python', prerequisite=None,
            course=course
        )
        return demo_quiz

    def __str__(self):
        desc = self.description or 'Quiz'
        return '%s: on %s for %d minutes' % (desc, self.start_date_time,
                                             self.duration)


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

    objects = QuestionPaperManager()

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
        return questions

    def make_answerpaper(self, user, ip, attempt_num):
        """Creates an  answer paper for the user to attempt the quiz"""
        ans_paper = AnswerPaper(
            user=user,
            user_ip=ip,
            attempt_number=attempt_num
        )
        ans_paper.start_time = timezone.now()
        ans_paper.end_time = ans_paper.start_time + \
            timedelta(minutes=self.quiz.duration)
        ans_paper.question_paper = self
        ans_paper.save()
        questions = self._get_questions_for_answerpaper()
        for question in questions:
            ans_paper.questions.add(question)
        for question in questions:
            ans_paper.questions_unanswered.add(question)
        return ans_paper

    def _is_questionpaper_passed(self, user):
        return AnswerPaper.objects.filter(question_paper=self, user=user,
                                          passed=True).exists()

    def _is_attempt_allowed(self, user):
        attempts = AnswerPaper.objects.get_total_attempt(questionpaper=self,
                                                         user=user)
        return attempts != self.quiz.attempts_allowed

    def can_attempt_now(self, user):
        if self._is_attempt_allowed(user):
            last_attempt = AnswerPaper.objects.get_user_last_attempt(
                user=user, questionpaper=self
            )
            if last_attempt:
                time_lag = (timezone.now() - last_attempt.start_time).days
                return time_lag >= self.quiz.time_between_attempts
            else:
                return True
        else:
            return False

    def _get_prequisite_paper(self):
        return self.quiz.prerequisite.questionpaper_set.get()

    def is_prerequisite_passed(self, user):
        if self.quiz.has_prerequisite():
            prerequisite = self._get_prequisite_paper()
            return prerequisite._is_questionpaper_passed(user)

    def create_demo_quiz_ppr(self, demo_quiz, user):
        question_paper = QuestionPaper.objects.create(quiz=demo_quiz,
                                                      total_marks=6.0,
                                                      shuffle_questions=True
                                                      )
        questions = Question.objects.filter(active=True,
                                            summary="Yaksh Demo Question",
                                            user=user)
        q_order = [str(que.id) for que in questions]
        question_paper.fixed_question_order = ",".join(q_order)
        question_paper.save()
        # add fixed set of questions to the question paper
        question_paper.fixed_questions.add(*questions)

    def get_ordered_questions(self):
        ques = []
        if self.fixed_question_order:
            que_order = self.fixed_question_order.split(',')
            for que_id in que_order:
                ques.append(self.fixed_questions.get(id=que_id))
        else:
            ques = self.fixed_questions.all()
        return ques

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
    def get_all_questions(self, questionpaper_id, attempt_number,
                          status='completed'):
        ''' Return a dict of question id as key and count as value'''
        papers = self.filter(question_paper_id=questionpaper_id,
                             attempt_number=attempt_number, status=status)
        all_questions = list()
        questions = list()
        for paper in papers:
            all_questions += paper.get_questions()
        for question in all_questions:
            questions.append(question.id)
        return Counter(questions)

    def get_all_questions_answered(self, questionpaper_id, attempt_number,
                                   status='completed'):
        ''' Return a dict of answered question id as key and count as value'''
        papers = self.filter(question_paper_id=questionpaper_id,
                             attempt_number=attempt_number, status=status)
        questions_answered = list()
        for paper in papers:
            for question in filter(None, paper.get_questions_answered()):
                if paper.is_answer_correct(question):
                    questions_answered.append(question.id)
        return Counter(questions_answered)

    def get_attempt_numbers(self, questionpaper_id, status='completed'):
        ''' Return list of attempt numbers'''
        attempt_numbers = self.filter(
            question_paper_id=questionpaper_id, status=status
        ).values_list('attempt_number', flat=True).distinct()
        return attempt_numbers

    def has_attempt(self, questionpaper_id, attempt_number,
                    status='completed'):
        ''' Whether question paper is attempted'''
        return self.filter(
            question_paper_id=questionpaper_id,
            attempt_number=attempt_number, status=status
        ).exists()

    def get_count(self, questionpaper_id, attempt_number, status='completed'):
        ''' Return count of answerpapers for a specfic question paper
            and attempt number'''
        return self.filter(
            question_paper_id=questionpaper_id,
            attempt_number=attempt_number, status=status
        ).count()

    def get_question_statistics(self, questionpaper_id, attempt_number,
                                status='completed'):
        ''' Return dict with question object as key and list as value
            The list contains two value, first the number of times a question
            was answered correctly, and second the number of times a question
            appeared in a quiz'''
        question_stats = {}
        questions_answered = self.get_all_questions_answered(questionpaper_id,
                                                             attempt_number)
        questions = self.get_all_questions(questionpaper_id, attempt_number)
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

    def _get_answerpapers_for_quiz(self, questionpaper_id, status=False):
        if not status:
            return self.filter(question_paper_id=questionpaper_id)
        else:
            return self.filter(question_paper_id=questionpaper_id,
                               status="completed")

    def _get_answerpapers_users(self, answerpapers):
        return answerpapers.values_list('user', flat=True).distinct()

    def get_latest_attempts(self, questionpaper_id):
        papers = self._get_answerpapers_for_quiz(questionpaper_id)
        users = self._get_answerpapers_users(papers)
        latest_attempts = []
        for user in users:
            latest_attempts.append(self._get_latest_attempt(papers, user))
        return latest_attempts

    def _get_latest_attempt(self, answerpapers, user_id):
        return answerpapers.filter(
            user_id=user_id
        ).order_by('-attempt_number')[0]

    def get_user_last_attempt(self, questionpaper, user):
        attempts = self.filter(question_paper=questionpaper,
                               user=user).order_by('-attempt_number')
        if attempts:
            return attempts[0]

    def get_user_answerpapers(self, user):
        return self.filter(user=user)

    def get_total_attempt(self, questionpaper, user):
        return self.filter(question_paper=questionpaper, user=user).count()

    def get_users_for_questionpaper(self, questionpaper_id):
        return self._get_answerpapers_for_quiz(questionpaper_id, status=True)\
            .values("user__id", "user__first_name", "user__last_name")\
            .distinct()

    def get_user_all_attempts(self, questionpaper, user):
        return self.filter(question_paper=questionpaper, user=user)\
                            .order_by('-attempt_number')

    def get_user_data(self, user, questionpaper_id, attempt_number=None):
        if attempt_number is not None:
            papers = self.filter(user=user, question_paper_id=questionpaper_id,
                                 attempt_number=attempt_number)
        else:
            papers = self.filter(
                user=user, question_paper_id=questionpaper_id
            ).order_by("-attempt_number")
        data = {}
        profile = user.profile if hasattr(user, 'profile') else None
        data['user'] = user
        data['profile'] = profile
        data['papers'] = papers
        data['questionpaperid'] = questionpaper_id
        return data

    def get_user_best_of_attempts_marks(self, quiz, user_id):
        best_attempt = 0.0
        papers = self.filter(question_paper__quiz=quiz,
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

    objects = AnswerPaperManager()

    def current_question(self):
        """Returns the current active question to display."""
        if self.questions_unanswered.all():
            return self.questions_unanswered.all()[0]

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

        next_question = self.next_question(question_id)
        if next_question and next_question.id == int(question_id):
            return None
        return next_question

    def next_question(self, question_id):
        """
            Skips the current question and returns the next sequentially
             available question.
        """
        all_questions = self.questions.all()
        unanswered_questions = self.questions_unanswered.all()
        questions = list(all_questions.values_list('id', flat=True))
        if len(questions) == 0:
            return None
        if unanswered_questions.count() == 0:
            return None
        try:
            index = questions.index(int(question_id))
            next_id = questions[index+1]
        except (ValueError, IndexError):
            next_id = questions[0]
        return all_questions.get(id=next_id)

    def time_left(self):
        """Return the time remaining for the user in seconds."""
        dt = timezone.now() - self.start_time
        try:
            secs = dt.total_seconds()
        except AttributeError:
            # total_seconds is new in Python 2.7. :(
            secs = dt.seconds + dt.days*24*3600
        total = self.question_paper.quiz.duration*60.0
        remain = max(total - secs, 0)
        return int(remain)

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
        if question.type == 'code':
            return self.answers.filter(question=question).order_by('-id')

    def validate_answer(self, user_answer, question, json_data=None):
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
                expected_answer = question.get_test_case(correct=True).options
                if user_answer.strip() == expected_answer.strip():
                    result['success'] = True
                    result['error'] = ['Correct answer']

            elif question.type == 'mcc':
                expected_answers = []
                for opt in question.get_test_cases(correct=True):
                    expected_answers.append(opt.options)
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
                tc_status = []
                for tc in question.get_test_cases():
                    if abs(tc.correct - user_answer) <= tc.error_margin:
                        tc_status.append(True)
                if any(tc_status):
                    result['success'] = True
                    result['error'] = ['Correct answer']

            elif question.type == 'code' or question.type == "upload":
                user_dir = self.user.profile.get_user_dir()
                json_result = code_server.run_code(
                    question.language, json_data, user_dir
                )
                result = json.loads(json_result)
        return result

    def regrade(self, question_id):
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
        if question.type == 'mcc':
            try:
                answer = eval(user_answer.answer)
                if type(answer) is not list:
                    return False, msg + 'MCC answer not a list.'
            except Exception:
                return False, msg + 'MCC answer submission error'
        else:
            answer = user_answer.answer
        json_data = question.consolidate_answer_data(answer) \
            if question.type == 'code' else None
        result = self.validate_answer(answer, question, json_data)
        user_answer.correct = result.get('success')
        user_answer.error = result.get('error')
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


###############################################################################
class AssignmentUpload(models.Model):
    user = models.ForeignKey(User)
    assignmentQuestion = models.ForeignKey(Question)
    assignmentFile = models.FileField(upload_to=get_assignment_dir)


###############################################################################
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
    string_check = models.CharField(max_length=200,choices=string_check_type)

    def get_field_value(self):
        return {"test_case_type": "stringtestcase", "correct": self.correct,
                "string_check":self.string_check}

    def __str__(self):
        return u'String Testcase | Correct: {0}'.format(self.correct)


class FloatTestCase(TestCase):
    correct = models.FloatField(default=None)
    error_margin = models.FloatField(default=0.0, null=True, blank=True,
                                     help_text="Margin of error")

    def get_field_value(self):
        return {"test_case_type": "floattestcase", "correct": self.correct,
                "error_margin":self.error_margin}

    def __str__(self):
        return u'Testcase | Correct: {0} | Error Margin: +or- {1}'.format(
                self.correct, self.error_margin
                )
